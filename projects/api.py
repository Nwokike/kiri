"""
API views for fetching user repositories from connected platforms.
"""
import logging
import requests
import json
import hashlib
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, login_not_required
from django.views.decorators.http import require_GET
from django.core.cache import cache
from users.models import UserIntegration

logger = logging.getLogger(__name__)


def fetch_github_repos(token):
    """Fetch repositories from GitHub."""
    repos = []
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.get(
            "https://api.github.com/user/repos?per_page=50&sort=updated&affiliation=owner",
            headers=headers,
            timeout=10
        )
        if response.ok:
            for repo in response.json():
                repos.append({
                    "id": f"github:{repo['full_name']}",
                    "platform": "github",
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", "") or "",
                    "url": repo["html_url"],
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language", ""),
                    "private": repo.get("private", False),
                })
        else:
            logger.warning(f"GitHub API returned {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repos: {e}")
    return repos




def fetch_huggingface_repos(token):
    """Fetch repositories (models/spaces) from Hugging Face."""
    repos = []
    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        # Fetch models
        response = requests.get(
            "https://huggingface.co/api/models?author=me&limit=25",
            headers=headers,
            timeout=10
        )
        if response.ok:
            for model in response.json():
                repos.append({
                    "id": f"huggingface:{model['modelId']}",
                    "platform": "huggingface",
                    "name": model["modelId"].split("/")[-1],
                    "full_name": model["modelId"],
                    "description": "",
                    "url": f"https://huggingface.co/{model['modelId']}",
                    "stars": model.get("likes", 0),
                    "language": "",
                    "private": model.get("private", False),
                    "type": "model",
                })
        
        # Fetch spaces
        response = requests.get(
            "https://huggingface.co/api/spaces?author=me&limit=25",
            headers=headers,
            timeout=10
        )
        if response.ok:
            for space in response.json():
                repos.append({
                    "id": f"huggingface:{space['id']}",
                    "platform": "huggingface",
                    "name": space["id"].split("/")[-1],
                    "full_name": space["id"],
                    "description": "",
                    "url": f"https://huggingface.co/spaces/{space['id']}",
                    "stars": space.get("likes", 0),
                    "language": "",
                    "private": space.get("private", False),
                    "type": "space",
                })
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace repos: {e}")
    return repos


@login_required
@require_GET
def user_repos_api(request):
    """
    API endpoint to fetch all repositories from user's connected platforms.
    Returns a JSON list of repositories.
    """
    # Check cache first
    cache_key = f"user_repos:{request.user.id}"
    cached = cache.get(cache_key)
    if cached and not request.GET.get("refresh"):
        return JsonResponse({"repos": cached, "cached": True})
    
    all_repos = []
    integrations = UserIntegration.objects.filter(user=request.user)
    
    for integration in integrations:
        token = integration.get_decrypted_access_token()
        if not token:
            continue
        
        if integration.platform == "github":
            all_repos.extend(fetch_github_repos(token))
        elif integration.platform == "huggingface":
            all_repos.extend(fetch_huggingface_repos(token))
    
    # Sort by most recently starred (as a proxy for importance)
    all_repos.sort(key=lambda x: x.get("stars", 0), reverse=True)
    
    # Cache for 5 minutes
    cache.set(cache_key, all_repos, 300)
    
    return JsonResponse({"repos": all_repos, "cached": False})


@login_required
def save_gist_api(request):
    """API to save code as a Gist."""
    # 4.3: Rate limiting (10 per minute per user)
    rate_key = f"gist_rate_{request.user.id}"
    if cache.get(rate_key, 0) >= 10:
        return JsonResponse({"error": "Rate limit exceeded. Please wait a minute."}, status=429)
    cache.set(rate_key, cache.get(rate_key, 0) + 1, 60)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        files = data.get("files")
        description = data.get("description", "Kiri Studio Snippet")
        public = data.get("public", True)
        
        if not files:
            return JsonResponse({"error": "No files provided"}, status=400)
            
        from .gist_service import GistService
        result = GistService.create_user_gist(request.user, files, description, public)
        
        if result:
            return JsonResponse(result)
        else:
            return JsonResponse({"error": "Failed to create Gist. Ensure GitHub is connected."}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Save Gist API Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@login_not_required
async def studio_ai_assist(request):
    """API for Kiri Studio AI assistance (Explain, Debug, Write)."""
    from asgiref.sync import sync_to_async
    
    # 4.3: Rate limiting (10 per minute per user/IP)
    # Wrap sync property access in sync_to_async
    is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
    
    if is_authenticated:
        user_id = await sync_to_async(lambda: request.user.id)()
        rate_key = f"ai_assist_rate_{user_id}"
    else:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        rate_key = f"ai_assist_rate_ip_{ip}"
        
    current_count = await sync_to_async(cache.get)(rate_key, 0)
    if current_count >= 10:
        return JsonResponse({"error": "Rate limit exceeded. Please wait a minute."}, status=429)
    await sync_to_async(cache.set)(rate_key, current_count + 1, 60)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        task = data.get("task") # 'explain', 'debug', 'write'
        code = data.get("code")
        context = data.get("context", "")
        
        if not code or not task:
            return JsonResponse({"error": "Missing code or task"}, status=400)
            
        # Construct primitive prompt for now (Phase 2.1 had better logic, reusing simple fallback)
        prompts = {
            "explain": f"Explain this code concisely:\n\n{code}",
            "debug": f"Find bugs in this code and suggest fixes:\n\n{code}\nContext: {context}",
            "write": f"Write code based on this request:\n\n{context}\n\nexisting code context:\n{code}"
        }
        
        prompt = prompts.get(task, f"Analyze this:\n{code}")
        
        # 3.3: Use unified AI service
        ai_service = get_ai_service()
        response = await ai_service.generate_json(prompt)
        
        # Parse JSON if call_ai returns JSON string, or just return text
        try:
            # AIService.generate_json_sync returns a dict or None
            if response is None:
                return JsonResponse({"error": "AI service failure"}, status=500)
            return JsonResponse({"result": response} if isinstance(response, str) else response)
        except Exception as e:
            return JsonResponse({"result": str(response)})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_GET
def repo_files_api(request):
    """
    API to fetch file list for a given repo URL.
    Used for selecting a file for Publications.
    """
    repo_url = request.GET.get('url')
    if not repo_url:
        return JsonResponse({"error": "Missing URL"}, status=400)
    
    from .services import GitHubService
    # 4.2: Validate and hash repo_url for cache key
    if not repo_url.startswith("https://github.com/"):
        return JsonResponse({"error": "Invalid repository URL. Only GitHub is supported for file listing."}, status=400)
    
    url_hash = hashlib.sha256(repo_url.encode()).hexdigest()
    cache_key = f"repo_files_{url_hash}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({"files": cached})
        
    try:
        data = GitHubService.fetch_structure(repo_url)
        if data and 'file_list' in data:
            files = data['file_list']
            # Filter for likely publication files (markdown, pdf, latex)
            # But return all is safer, let frontend filter
            cache.set(cache_key, files, 300)
            return JsonResponse({"files": files})
        return JsonResponse({"files": []})
    except Exception as e:
        logger.error(f"Repo Files API Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
