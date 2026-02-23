"""
AI Service for Kiri Labs.
Multi-provider AI with Groq (free) primary + Gemini fallback.
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
    AI service with multi-model fallback chain.
    Used for project analysis (ProjectInsight) and audio transcription.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Model priority: free Groq first, then paid Gemini
    AI_MODELS = [
        {"provider": "groq", "model": "moonshotai/kimi-k2-instruct-0905"},
        {"provider": "groq", "model": "moonshotai/kimi-k2-instruct"},
        {"provider": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct"},
        {"provider": "groq", "model": "meta-llama/llama-4-maverick-17b-128e-instruct"},
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
        {"provider": "groq", "model": "qwen/qwen3-32b"},
        {"provider": "groq", "model": "openai/gpt-oss-20b"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "gemini", "model": "gemini-3-flash"},
        {"provider": "gemini", "model": "gemini-2.5-flash"},
        {"provider": "gemini", "model": "gemini-2.5-flash-lite"},
        {"provider": "gemini", "model": "gemini-3-pro"},
        {"provider": "gemini", "model": "gemini-2.5-pro"},
        {"provider": "groq", "model": "llama-3.1-8b-instant"},
    ]

    @classmethod
    def generate_json_sync(cls, prompt: str, requested_model: Optional[str] = None, simple_task: bool = False) -> Optional[dict]:
        """
        Rotates through models until a valid JSON response is received.
        If requested_model is provided, it tries that first.
        """
        model_list = cls.AI_MODELS
        if requested_model and requested_model != 'auto':
            req_cfg = next((m for m in cls.AI_MODELS if m['model'] == requested_model), None)
            if req_cfg:
                model_list = [req_cfg] + [m for m in cls.AI_MODELS if m['model'] != requested_model]
            else:
                model_list = [{"provider": "groq", "model": requested_model}] + cls.AI_MODELS

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
    async def generate_json(cls, prompt: str, requested_model: Optional[str] = None, simple_task: bool = False) -> Optional[dict]:
        """Async wrapper for generate_json_sync."""
        return await sync_to_async(cls.generate_json_sync)(prompt, requested_model=requested_model, simple_task=simple_task)

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
        """Call Gemini API."""
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
        """Call Groq API."""
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
    async def transcribe_audio(cls, audio_file, model: str = "whisper-large-v3-turbo") -> Optional[str]:
        """Transcribe audio using Groq Whisper."""
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key: return None

        try:
            def _call():
                files = {'file': (audio_file.name, audio_file.read(), audio_file.content_type)}
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                    data={"model": model},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get('text')
                return None

            return await sync_to_async(_call)()
        except Exception as e:
            logger.error(f"Transcription failure: {e}")
            return None


def get_ai_service():
    return AIService