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
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service with Gemini primary + Groq fallback.
    Uses HTTP requests directly (no heavy SDK) for memory efficiency.
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
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
        Classifies a repository into an execution lane.
        
        Args:
            repo_files: Dict with 'file_list', 'package_json', 'requirements_txt' keys
            
        Returns:
            Dict with 'lane', 'reason', 'start_command' keys
        """
        prompt = cls.CLASSIFICATION_PROMPT.format(
            file_list=json.dumps(repo_files.get('file_list', [])[:50]),  # Limit file list
            package_json=repo_files.get('package_json', 'Not found')[:1500],
            requirements_txt=repo_files.get('requirements_txt', 'Not found')[:1500],
            pyproject_toml=repo_files.get('pyproject_toml', 'Not found')[:1000],
            dockerfile=repo_files.get('dockerfile', 'Not found')[:800],
            main_file=repo_files.get('main_file', 'Not found')[:800],
            readme=repo_files.get('readme', 'Not found')[:500]
        )
        
        # Try Gemini first
        result = cls._call_gemini(prompt)
        
        # Fallback to Groq if Gemini fails
        if result is None:
            logger.warning("Gemini failed, falling back to Groq")
            result = cls._call_groq(prompt)
        
        # Ultimate fallback - heuristic classification
        if result is None:
            logger.warning("Both AI services failed, using heuristic fallback")
            result = cls._heuristic_classification(repo_files)
        
        # Validate and correct AI result with heuristics if it seems wrong
        result = cls._validate_classification(result, repo_files)
        
        return result
    
    @classmethod
    def _validate_classification(cls, result: dict, repo_files: dict) -> dict:
        """Validate AI classification with heuristics to catch obvious mistakes."""
        requirements = repo_files.get('requirements_txt', '').lower()
        package_json = repo_files.get('package_json', '')
        
        # If requirements.txt has django/flask but AI said Lane A, correct it
        backend_keywords = ['django', 'flask', 'fastapi', 'uvicorn', 'gunicorn']
        if any(kw in requirements for kw in backend_keywords) and result.get('lane') == 'A':
            logger.info("Correcting classification: Python backend detected, switching to Lane B")
            return cls._heuristic_classification(repo_files)
        
        # If requirements.txt has torch/transformers but AI said Lane A or B, correct it
        gpu_keywords = ['torch', 'tensorflow', 'transformers', 'keras', 'jax']
        if any(kw in requirements for kw in gpu_keywords) and result.get('lane') in ['A', 'B']:
            logger.info("Correcting classification: ML/GPU project detected, switching to Lane C")
            return cls._heuristic_classification(repo_files)
        
        return result
    
    @classmethod
    def _clean_json_response(cls, text: str) -> str:
        """Clean AI response to extract valid JSON."""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith('```'):
            # Handle ```json or just ```
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]  # Remove opening ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]  # Remove closing ```
            text = '\n'.join(lines)
        
        # Find JSON object in text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            text = text[start:end]
        
        return text.strip()
    
    @classmethod
    def _call_gemini(cls, prompt: str) -> Optional[dict]:
        """Call Gemini 2.5 Flash API."""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not set")
            return None
        
        try:
            response = requests.post(
                f"{cls.GEMINI_API_URL}?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 256,
                    }
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 429:
                logger.warning("Gemini rate limit hit")
                return None
            
            if response.status_code != 200:
                logger.error(f"Gemini error: {response.status_code} - {response.text[:200]}")
                return None
            
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Clean and parse JSON
            text = cls._clean_json_response(text)
            
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Gemini JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    @classmethod
    def _call_groq(cls, prompt: str) -> Optional[dict]:
        """Call Groq API as fallback."""
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            logger.error("GROQ_API_KEY not set")
            return None
        
        try:
            response = requests.post(
                cls.GROQ_API_URL,
                json={
                    # llama-3.3-70b-versatile: GPT-4 class intelligence
                    # Best quality for classification, supports JSON mode
                    # Rate limits: ~6k TPM (sufficient for fallback usage)
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{
                        "role": "system",
                        "content": "You are an expert at analyzing code repositories. Respond ONLY with valid JSON, no explanations."
                    }, {
                        "role": "user", 
                        "content": prompt
                    }],
                    # JSON Object Mode - guarantees syntactically valid JSON
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 256,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 429:
                logger.warning("Groq rate limit hit")
                return None
            
            if response.status_code != 200:
                logger.error(f"Groq error: {response.status_code} - {response.text[:200]}")
                return None
            
            data = response.json()
            text = data['choices'][0]['message']['content']
            
            # Clean and parse JSON
            text = cls._clean_json_response(text)
            
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            logger.error(f"Groq JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    @classmethod
    def _heuristic_classification(cls, repo_files: dict) -> dict:
        """Fallback heuristic when AI services fail."""
        files = repo_files.get('file_list', [])
        package_json = repo_files.get('package_json', '')
        requirements = repo_files.get('requirements_txt', '').lower()
        
        # Lane C indicators (GPU/ML)
        gpu_keywords = ['torch', 'tensorflow', 'transformers', 'keras', 'jax', 'cuda']
        if any(kw in requirements for kw in gpu_keywords):
            return {
                'lane': 'C',
                'reason': 'Contains ML/AI libraries requiring GPU',
                'start_command': 'python train.py'
            }
        
        # Lane B indicators (Python backend)
        backend_keywords = ['django', 'flask', 'fastapi', 'uvicorn', 'gunicorn']
        if any(kw in requirements for kw in backend_keywords):
            if 'django' in requirements:
                return {
                    'lane': 'B',
                    'reason': 'Django web application',
                    'start_command': 'python manage.py runserver 0.0.0.0:8000'
                }
            return {
                'lane': 'B',
                'reason': 'Python web backend',
                'start_command': 'python app.py'
            }
        
        # Lane A indicators - SLM/Browser ML (transformers.js, Pyodide)
        slm_keywords = ['@xenova/transformers', 'transformers.js', '@huggingface/transformers']
        pyodide_keywords = ['pyodide', 'gradio-lite', 'pyscript']
        
        package_json_lower = package_json.lower()
        if any(kw in package_json_lower for kw in slm_keywords):
            return {
                'lane': 'A',
                'reason': 'Browser-runnable ML using transformers.js',
                'start_command': 'npm run dev'
            }
        
        if any(kw in requirements for kw in pyodide_keywords):
            return {
                'lane': 'A',
                'reason': 'Browser-runnable Python using Pyodide',
                'start_command': ''
            }
        
        # Lane A indicators (Frontend/Node)
        if package_json or any(f.endswith('.jsx') or f.endswith('.tsx') for f in files):
            return {
                'lane': 'A',
                'reason': 'JavaScript/Node.js project',
                'start_command': 'npm run dev'
            }
        
        # Default: static/simple project
        return {
            'lane': 'A',
            'reason': 'Simple static or browser-runnable project',
            'start_command': ''
        }
    
    @classmethod
    def generate_colab_notebook(cls, repo_url: str, entry_point: str = '') -> str:
        """
        Generates a Colab notebook JSON for Lane C projects.
        
        Returns:
            JSON string representing the .ipynb notebook
        """
        # Parse repo owner and name
        parts = repo_url.rstrip('/').split('/')
        repo_name = parts[-1].replace('.git', '')
        
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 0,
            "metadata": {
                "colab": {"name": f"{repo_name}_demo.ipynb"},
                "kernelspec": {"name": "python3", "display_name": "Python 3"}
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": [f"# {repo_name}\n\nThis notebook was auto-generated by [Kiri Research Labs](https://kiri.ng) to help you run this project."],
                    "metadata": {}
                },
                {
                    "cell_type": "code",
                    "source": [
                        f"# Clone the repository\n",
                        f"!git clone {repo_url}\n",
                        f"%cd {repo_name}"
                    ],
                    "metadata": {},
                    "execution_count": None,
                    "outputs": []
                },
                {
                    "cell_type": "code",
                    "source": [
                        "# Install dependencies\n",
                        "!pip install -r requirements.txt"
                    ],
                    "metadata": {},
                    "execution_count": None,
                    "outputs": []
                },
                {
                    "cell_type": "code",
                    "source": [
                        f"# Run the project\n",
                        f"# {entry_point if entry_point else 'Modify this cell to run your specific script'}"
                    ],
                    "metadata": {},
                    "execution_count": None,
                    "outputs": []
                }
            ]
        }
        
        return json.dumps(notebook, indent=2)
