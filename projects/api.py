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
