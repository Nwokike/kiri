"""
AI Service for Traffic Controller
Provides project classification using Gemini 2.5 Flash (primary) + Groq (fallback).
Designed for minimal memory footprint on 1GB RAM constraint.
"""

import os
import json
import logging
import requests
from typing import Optional
from asgiref.sync import sync_to_async

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
                if isinstance(result, dict):
                    result['_ai_model'] = model_id
                return result
                
        logger.error("All AI models in the fallback chain failed.")
        return None

    @classmethod
    async def generate_json(cls, prompt: str, simple_task: bool = False) -> Optional[dict]:
        """Async wrapper for generate_json_sync."""
        return await sync_to_async(cls.generate_json_sync)(prompt, simple_task=simple_task)
    
    # Classification prompt - Updated for Dual-Studio Architecture (PyStudio vs JS Studio)
    CLASSIFICATION_PROMPT = """Analyze this GitHub repository to determine the best execution environment.

**Assign to ONE lane:**
- 'P' (PyStudio): Pure Python scripts, Data Science (Pandas/Numpy), Matplotlib, Jupyter Notebooks (converted), Algorithm demos. NO heavy servers (Django/Flask). NO GPU.
- 'J' (JS Studio): Node.js, React, Vue, Svelte, Vite, Next.js, Static HTML/CSS/JS, Express.js (simple). Client-side Node environment (WebContainers).
- 'B' (Binder/Cloud): Complex Backend Servers (Django, Flask, FastAPI, Rails, Go, Rust), Docker-based projects, Databases (Postgres/Redis required).
- 'C' (Colab/GPU): Deep Learning, PyTorch, TensorFlow, Transformers, LLMs, CUDA, Heavy AI training.

**Repository Analysis:**
File Structure: {file_list}
package.json: {package_json}
requirements.txt: {requirements_txt}
pyproject.toml: {pyproject_toml}
Dockerfile: {dockerfile}
Main entry file: {main_file}
README excerpt: {readme}

**Return ONLY valid JSON:**
{{"lane": "P", "reason": "Brief explanation", "start_command": "python main.py"}}

**Decision Rules:**
1. Has torch/tensorflow/transformers/jax → Lane C (GPU required)
2. Has django/flask/fastapi/uvicorn/gunicorn → Lane B (Server required)
3. Has Dockerfile → Lane B (Container required)
4. Has package.json + (react/vue/svelte/vite/next) → Lane J (JS Studio)
5. Has requirements.txt but NO web frameworks/GPU → Lane P (PyStudio)
6. Pure HTML/CSS/JS → Lane J
7. Simple Python script → Lane P"""

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
        package_json = repo_files.get('package_json', '')
        
        # 1. Catch Hidden Backends (Python)
        backend_keywords = ['django', 'flask', 'fastapi', 'uvicorn', 'gunicorn']
        if any(kw in requirements for kw in backend_keywords) and result.get('lane') in ['P', 'J']:
            logger.info("Correction: Python backend detected -> Lane B")
            return {'lane': 'B', 'reason': 'Correction: Python backend requires Cloud Container', 'start_command': 'python manage.py runserver'}
            
        # 2. Catch Hidden GPU/ML
        gpu_keywords = ['torch', 'tensorflow', 'transformers', 'keras', 'jax']
        if any(kw in requirements for kw in gpu_keywords) and result.get('lane') in ['P', 'J', 'B']:
            logger.info("Correction: GPU deps detected -> Lane C")
            return {'lane': 'C', 'reason': 'Correction: ML workload requires GPU', 'start_command': ''}

        # 3. Catch Node.js sent to Python Lane
        if package_json and result.get('lane') == 'P':
             logger.info("Correction: Node.js project -> Lane J")
             return {'lane': 'J', 'reason': 'Correction: package.json found', 'start_command': 'npm run dev'}

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
        
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){model}:generateContent"
        
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
        
        # New Distinction: Node vs Python
        if package_json or any(f.endswith(('.jsx', '.tsx', '.js')) for f in files):
            return {'lane': 'J', 'reason': 'Heuristic: JS/Node detected', 'start_command': 'npm run dev'}
        
        return {'lane': 'P', 'reason': 'Heuristic: Defaulting to PyStudio', 'start_command': 'python main.py'}
    
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