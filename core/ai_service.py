"""
AI Service for Traffic Controller
Provides project classification using Gemini 2.5 Flash (primary) + Groq (fallback).
Designed for minimal memory footprint on 1GB RAM constraint.
"""

import os
import json
import logging
import requests
import json
from typing import Optional
from asgiref.sync import sync_to_async
from typing import Optional

logger = logging.getLogger(__name__)


class AIService:
    """
    Traffic Controller AI service.
    Handles repository lane classification and content generation.
    Supports a 15+ model fallback chain prioritizing free resources.
    """
    
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Priority tiers for AI operations
    # Order: Moonshot K2 -> Llama 4 -> GPT OSS -> Qwen -> Versatile -> Gemini Tiers
    AI_MODELS = [
        # --- GROQ TIERS (Primary / Free) ---
        {"provider": "groq", "model": "moonshotai/kimi-k2-instruct-0905"},
        {"provider": "groq", "model": "moonshotai/kimi-k2-instruct"},
        {"provider": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
        {"provider": "groq", "model": "meta-llama/llama-4-maverick-17b-128e-instruct"},
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
        {"provider": "groq", "model": "qwen/qwen3-32b"},
        {"provider": "groq", "model": "openai/gpt-oss-20b"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        
        # --- GEMINI TIERS (Paid / High Fidelity) ---
        {"provider": "gemini", "model": "gemini-3-flash"},
        {"provider": "gemini", "model": "gemini-2.5-flash"},
        {"provider": "gemini", "model": "gemini-2.5-flash-lite"},
        {"provider": "gemini", "model": "gemini-3-pro"},
        {"provider": "gemini", "model": "gemini-2.5-pro"},

        # --- ABSOLUTE LAST RESORT ---
        {"provider": "groq", "model": "llama-3.1-8b-instant"},
    ]

    @classmethod
    def generate_json_sync(cls, prompt: str, simple_task: bool = False) -> Optional[dict]:
        """
        Rotates through models until a valid JSON response is received.
        """
        model_list = cls.AI_MODELS
        # We no longer reorder for simple tasks to ensure the last resort stays last.
        
        for model_cfg in model_list:
            provider = model_cfg['provider']
            model_id = model_cfg['model']
            
            logger.info(f"Attempting AI task with {model_id} ({provider})")
            
            result = None
            if provider == "groq":
                result = cls._call_groq(prompt, model=model_id)
            elif provider == "gemini":
                result = cls._call_gemini(prompt, model=model_id)
                
            if result:
                # Store which model was used in the result for tracking
                if isinstance(result, dict):
                    result['_ai_model'] = model_id
                return result
                
        logger.error("All AI models in the fallback chain failed.")
        return None

    @classmethod
    async def generate_json(cls, prompt: str, simple_task: bool = False) -> Optional[dict]:
        """Async wrapper for generate_json_sync."""
        return await sync_to_async(cls.generate_json_sync)(prompt, simple_task=simple_task)
    
    # Classification prompt - carefully crafted for consistent JSON output
    CLASSIFICATION_PROMPT = """Analyze this GitHub repository to determine the best execution environment.

**Assign to ONE lane:**
- 'A' (Client-Side/Browser): Static HTML/CSS/JS, Node.js, React, Vue, Angular, Svelte, Vite, simple Python scripts runnable in browser
- 'B' (Binder/Server): Django, Flask, FastAPI, Express, Docker, Go, Rust servers, databases, complex Python backends
- 'C' (Colab/GPU): PyTorch, TensorFlow, Transformers, JAX, ML training, LLMs, CUDA, heavy AI workloads

**Repository Analysis:**
File Structure: {file_list}
package.json: {package_json}
requirements.txt: {requirements_txt}
pyproject.toml: {pyproject_toml}
Dockerfile: {dockerfile}
Main entry file: {main_file}
README excerpt: {readme}

**Return ONLY valid JSON:**
{{"lane": "A", "reason": "Brief explanation of why this lane fits", "start_command": "npm run dev"}}

**Decision Rules:**
1. Has torch/tensorflow/transformers/keras/jax in deps → Lane C
2. Has django/flask/fastapi/uvicorn in deps → Lane B  
3. Has Dockerfile with exposed ports → Lane B
4. Has react/vue/vite/svelte in package.json → Lane A
5. Pure HTML/CSS/JS with no backend → Lane A
6. Python with no web framework or ML → Lane A (Pyodide)
7. Unsure → default to Lane B (safest)"""

    @classmethod
    def classify_repository_lane(cls, repo_files: dict) -> dict:
        """
        Classifies a repository using the multi-tier fallback system.
        """
        prompt = cls.CLASSIFICATION_PROMPT.format(
            file_list=json.dumps(repo_files.get('file_list', [])[:50]),
            package_json=repo_files.get('package_json', 'Not found')[:1500],
            requirements_txt=repo_files.get('requirements_txt', 'Not found')[:1500],
            pyproject_toml=repo_files.get('pyproject_toml', 'Not found')[:1000],
            dockerfile=repo_files.get('dockerfile', 'Not found')[:800],
            main_file=repo_files.get('main_file', 'Not found')[:800],
            readme=repo_files.get('readme', 'Not found')[:500]
        )
        
        # Use our robust rotation logic
        result = cls.generate_json_sync(prompt)
        
        # Ultimate fallback - heuristic classification
        if result is None:
            logger.warning("All AI models failed during classification, using heuristic fallback")
            result = cls._heuristic_classification(repo_files)
        
        # Validate and correct AI result with heuristics
        result = cls._validate_classification(result, repo_files)
        
        return result
    
    @classmethod
    def _validate_classification(cls, result: dict, repo_files: dict) -> dict:
        """Validate AI classification with heuristics to catch obvious mistakes."""
        requirements = repo_files.get('requirements_txt', '').lower()
        
        # If requirements.txt has django/flask but AI said Lane A, correct it
        backend_keywords = ['django', 'flask', 'fastapi', 'uvicorn', 'gunicorn']
        if any(kw in requirements for kw in backend_keywords) and result.get('lane') == 'A':
            logger.info("Correcting classification: Python backend detected, switching to Lane B")
            fallback = cls._heuristic_classification(repo_files)
            fallback['_ai_model'] = result.get('_ai_model', 'heuristic-corrected')
            return fallback
        
        # If requirements.txt has torch/transformers but AI said Lane A or B, correct it
        gpu_keywords = ['torch', 'tensorflow', 'transformers', 'keras', 'jax']
        if any(kw in requirements for kw in gpu_keywords) and result.get('lane') in ['A', 'B']:
            logger.info("Correcting classification: ML/GPU project detected, switching to Lane C")
            fallback = cls._heuristic_classification(repo_files)
            fallback['_ai_model'] = result.get('_ai_model', 'heuristic-corrected')
            return fallback
        
        return result
    
    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        """Clean AI response to extract valid JSON."""
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            text = text[start:end]
        return text.strip()
    
    @classmethod
    def _call_gemini(cls, prompt: str, model: str = "gemini-2.5-flash") -> Optional[dict]:
        """Call specific Gemini model API."""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return None
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        try:
            response = requests.post(
                f"{url}?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 512,
                    }
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 429:
                return None
            
            if response.status_code != 200:
                logger.error(f"Gemini {model} error: {response.status_code}")
                return None
            
            data = response.json()
            candidates = data.get('candidates')
            if not candidates: return None
            
            parts = candidates[0].get('content', {}).get('parts')
            if not parts: return None
                
            text = parts[0].get('text', '')
            if not text: return None
            
            return json.loads(cls._clean_json_response(text))
            
        except Exception as e:
            logger.error(f"Gemini {model} failure: {e}")
            return None
    
    @classmethod
    def _call_groq(cls, prompt: str, model: str = "llama-3.3-70b-versatile") -> Optional[dict]:
        """Call specific Groq model API."""
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            return None
        
        try:
            response = requests.post(
                cls.GROQ_API_URL,
                json={
                    "model": model,
                    "messages": [{
                        "role": "system",
                        "content": "Respond ONLY with valid JSON."
                    }, {
                        "role": "user", 
                        "content": prompt
                    }],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 512,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 429:
                logger.warning(f"Groq {model} rate limit hit")
                return None
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            choices = data.get('choices')
            if not choices: return None
                
            text = choices[0].get('message', {}).get('content', '')
            if not text: return None
            
            return json.loads(cls._clean_json_response(text))
        
        except Exception as e:
            logger.error(f"Groq {model} failure: {e}")
            return None
    
    @classmethod
    def _heuristic_classification(cls, repo_files: dict) -> dict:
        """Fallback heuristic when all AI services fail."""
        files = repo_files.get('file_list', [])
        package_json = repo_files.get('package_json', '')
        requirements = repo_files.get('requirements_txt', '').lower()
        
        gpu_keywords = ['torch', 'tensorflow', 'transformers', 'keras', 'jax', 'cuda']
        if any(kw in requirements for kw in gpu_keywords):
            return {'lane': 'C', 'reason': 'Heuristic: GPU/ML detected', 'start_command': 'python train.py'}
        
        backend_keywords = ['django', 'flask', 'fastapi', 'uvicorn', 'gunicorn']
        if any(kw in requirements for kw in backend_keywords):
            return {'lane': 'B', 'reason': 'Heuristic: Python backend detected', 'start_command': 'python manage.py runserver 0.0.0.0:8000'}
        
        if package_json or any(f.endswith(('.jsx', '.tsx')) for f in files):
            return {'lane': 'A', 'reason': 'Heuristic: JS/Node detected', 'start_command': 'npm run dev'}
        
        return {'lane': 'A', 'reason': 'Heuristic: Defaulting to Browser mode', 'start_command': ''}
    
    @classmethod
    def generate_colab_notebook(cls, repo_url: str, entry_point: str = '') -> str:
        """Generates a Colab notebook JSON for Lane C projects."""
        parts = repo_url.rstrip('/').split('/')
        repo_name = parts[-1].replace('.git', '')
        notebook = {
            "nbformat": 4, "nbformat_minor": 0,
            "metadata": {"colab": {"name": f"{repo_name}_demo.ipynb"}, "kernelspec": {"name": "python3", "display_name": "Python 3"}},
            "cells": [
                {"cell_type": "markdown", "source": [f"# {repo_name}\n\nGenerated by [Kiri](https://kiri.ng)"], "metadata": {}},
                {"cell_type": "code", "source": [f"!git clone {repo_url}\n", f"%cd {repo_name}"], "metadata": {}, "execution_count": None, "outputs": []},
                {"cell_type": "code", "source": ["!pip install -r requirements.txt"], "metadata": {}, "execution_count": None, "outputs": []},
                {"cell_type": "code", "source": [f"!{entry_point}" if entry_point else "# Manual start required"], "metadata": {}, "execution_count": None, "outputs": []}
            ]
        }
        return json.dumps(notebook, indent=2)

def get_ai_service():
    return AIService
