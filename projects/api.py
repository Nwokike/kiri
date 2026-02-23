"""
API views for fetching user repositories from connected platforms.
"""
import logging
import hashlib
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.cache import cache
from users.models import UserIntegration
from .models import Project

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
            "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator,organization_member",
            headers=headers,
            timeout=10
        )
        if response.ok:
            data = response.json()
            logger.info(f"GitHub API returned {len(data)} repositories.")
            for repo in data:
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
            logger.warning(f"GitHub API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to fetch GitHub repos: {e}")
    return repos


def fetch_huggingface_repos(token):
    """Fetch repositories (models/spaces) from Hugging Face."""
    repos = []
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Models
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
        # Spaces
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
    Supports ?platform=github or ?platform=huggingface filtering.
    """
    platform_filter = request.GET.get("platform")
    refresh = request.GET.get("refresh")
    
    cache_key = f"user_repos:{request.user.id}:{platform_filter or 'all'}"
    cached = cache.get(cache_key)
    if cached and not refresh:
        return JsonResponse({"repos": cached, "cached": True})
    
    all_repos = []
    
    # Self-healing integration sync
    from allauth.socialaccount.models import SocialToken, SocialAccount, SocialLogin
    from users.adapter import KiriSocialAccountAdapter
    
    adapter = KiriSocialAccountAdapter()
    accounts = SocialAccount.objects.filter(user=request.user)
    if platform_filter:
        accounts = accounts.filter(provider=platform_filter)
    
    for account in accounts:
        integration = UserIntegration.objects.filter(user=request.user, platform=account.provider).first()
        if not integration:
            logger.info(f"Self-healing: Creating missing integration for {account.provider}")
            sl = SocialLogin(user=request.user, account=account)
            st = SocialToken.objects.filter(account=account).first()
            if st:
                sl.token = st
                adapter._create_or_update_integration(request.user, sl)
    
    integrations = UserIntegration.objects.filter(user=request.user)
    if platform_filter:
        integrations = integrations.filter(platform=platform_filter)

    for integration in integrations:
        token = integration.get_decrypted_access_token()
        if not token:
            continue
        if integration.platform == "github":
            all_repos.extend(fetch_github_repos(token))
        elif integration.platform == "huggingface":
            all_repos.extend(fetch_huggingface_repos(token))
    
    all_repos.sort(key=lambda x: x.get("stars", 0), reverse=True)
    cache.set(cache_key, all_repos, 300)
    
    return JsonResponse({"repos": all_repos, "cached": False})


@login_required
@require_GET
def repo_files_api(request):
    """API to fetch file list for a given repo URL."""
    repo_url = request.GET.get('url')
    if not repo_url:
        return JsonResponse({"error": "Missing URL"}, status=400)
    
    from .services import GitHubService
    if not repo_url.startswith("https://github.com/"):
        return JsonResponse({"error": "Invalid repository URL. Only GitHub is supported."}, status=400)
    
    url_hash = hashlib.sha256(repo_url.encode()).hexdigest()
    cache_key = f"repo_files_{url_hash}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({"files": cached})
        
    try:
        data = GitHubService.fetch_structure(repo_url)
        if data and 'file_list' in data:
            files = data['file_list']
            cache.set(cache_key, files, 300)
            return JsonResponse({"files": files})
        return JsonResponse({"files": []})
    except Exception as e:
        logger.error(f"Repo Files API Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)