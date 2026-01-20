"""
API views for fetching user repositories from connected platforms.
"""
import logging
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
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


def fetch_gitlab_repos(token):
    """Fetch repositories from GitLab."""
    repos = []
    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        response = requests.get(
            "https://gitlab.com/api/v4/projects?owned=true&per_page=50&order_by=updated_at",
            headers=headers,
            timeout=10
        )
        if response.ok:
            for repo in response.json():
                repos.append({
                    "id": f"gitlab:{repo['path_with_namespace']}",
                    "platform": "gitlab",
                    "name": repo["name"],
                    "full_name": repo["path_with_namespace"],
                    "description": repo.get("description", "") or "",
                    "url": repo["web_url"],
                    "stars": repo.get("star_count", 0),
                    "language": "",  # GitLab doesn't include this in basic response
                    "private": repo.get("visibility") == "private",
                })
        else:
            logger.warning(f"GitLab API returned {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to fetch GitLab repos: {e}")
    return repos


def fetch_bitbucket_repos(token):
    """Fetch repositories from Bitbucket."""
    repos = []
    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        response = requests.get(
            "https://api.bitbucket.org/2.0/user/permissions/repositories?pagelen=50",
            headers=headers,
            timeout=10
        )
        if response.ok:
            for perm in response.json().get("values", []):
                repo = perm.get("repository", {})
                repos.append({
                    "id": f"bitbucket:{repo.get('full_name', '')}",
                    "platform": "bitbucket",
                    "name": repo.get("name", ""),
                    "full_name": repo.get("full_name", ""),
                    "description": repo.get("description", "") or "",
                    "url": repo.get("links", {}).get("html", {}).get("href", ""),
                    "stars": 0,  # Bitbucket doesn't have stars
                    "language": repo.get("language", ""),
                    "private": repo.get("is_private", False),
                })
        else:
            logger.warning(f"Bitbucket API returned {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to fetch Bitbucket repos: {e}")
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
        token = integration.access_token
        if not token:
            continue
        
        if integration.platform == "github":
            all_repos.extend(fetch_github_repos(token))
        elif integration.platform == "gitlab":
            all_repos.extend(fetch_gitlab_repos(token))
        elif integration.platform == "bitbucket":
            all_repos.extend(fetch_bitbucket_repos(token))
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


@login_required
def studio_ai_assist(request):
    """API for Kiri Studio AI assistance (Explain, Debug, Write)."""
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
        
        # Reuse the AI Advisor logic if possible, or simple direct call
        # For speed/simplicity here, we'll try to import the service helper
        from .ai_advisor import call_ai
        
        # We need to await? No, call_ai is async but Django view is sync unless async def
        # wrapper. Let's make this view async or use async_to_sync
        from asgiref.sync import async_to_sync
        response = async_to_sync(call_ai)(prompt)
        
        # Parse JSON if call_ai returns JSON string, or just return text
        try:
            # call_ai might return a dict or string depending on implementation
            if isinstance(response, str):
                return JsonResponse({"result": response})
            return JsonResponse(response)
        except:
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
    # Fetch structure (cached inside service if implemented, or we cache here)
    cache_key = f"repo_files_{repo_url}"
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
