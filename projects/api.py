"""
API views for fetching user repositories from connected platforms.
And providing Studio sync capabilities.
"""
import logging
import requests
import json
import hashlib
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.contrib.auth.decorators import login_required, login_not_required
from django.views.decorators.http import require_POST, require_GET
from django.core.cache import cache
from django.utils import timezone
from users.models import UserIntegration
from .services import GitHubService
from .models import Project
from core.ai_service import get_ai_service

logger = logging.getLogger(__name__)


def fetch_github_repos(token):
    """Fetch repositories from GitHub."""
    repos = []
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        # Broaden affiliation to catch more repos
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
    Supports ?platform=github or ?platform=huggingface filtering.
    """
    platform_filter = request.GET.get("platform")
    refresh = request.GET.get("refresh")
    
    # Check cache first
    cache_key = f"user_repos:{request.user.id}:{platform_filter or 'all'}"
    cached = cache.get(cache_key)
    if cached and not refresh:
        return JsonResponse({"repos": cached, "cached": True})
    
    all_repos = []
    
    # Audit 4.1: Self-healing integration sync
    from allauth.socialaccount.models import SocialToken, SocialAccount
    from allauth.socialaccount.models import SocialLogin
    from users.adapter import KiriSocialAccountAdapter
    
    adapter = KiriSocialAccountAdapter()
    
    # Filter social accounts based on requested platform
    accounts = SocialAccount.objects.filter(user=request.user)
    if platform_filter:
        accounts = accounts.filter(provider=platform_filter)
    
    for account in accounts:
        # Check if UserIntegration exists
        integration = UserIntegration.objects.filter(user=request.user, platform=account.provider).first()
        if not integration:
            logger.info(f"Self-healing: Creating missing integration for {account.provider}")
            sl = SocialLogin(user=request.user, account=account)
            st = SocialToken.objects.filter(account=account).first()
            if st:
                sl.token = st
                adapter._create_or_update_integration(request.user, sl)
    
    # Fetch integrations after potential healing
    integrations = UserIntegration.objects.filter(user=request.user)
    if platform_filter:
        integrations = integrations.filter(platform=platform_filter)

    logger.info(f"Fetching repos for {integrations.count()} platforms for {request.user.username}")
    
    for integration in integrations:
        token = integration.get_decrypted_access_token()
        if not token:
            logger.warning(f"No token found for {integration.platform} integration of {request.user.username}")
            continue
        
        if integration.platform == "github":
            github_repos = fetch_github_repos(token)
            all_repos.extend(github_repos)
        elif integration.platform == "huggingface":
            hf_repos = fetch_huggingface_repos(token)
            all_repos.extend(hf_repos)
    
    # Sort by stars
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
        # Check if it's a multipart (file upload) or JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            task = data.get("task")
            code = data.get("code")
            context = data.get("context", "")
            data_sample = data.get("data", "")
            language = data.get("language", "python")
            requested_model = data.get("requested_model")
        else:
            task = request.POST.get("task")
            requested_model = request.POST.get("requested_model")
            # For transcription, we handle FILES
            if task == 'transcribe' and 'file' in request.FILES:
                audio_file = request.FILES['file']
                ai_service = get_ai_service()
                # AIService doesn't have _call_whisper yet, we'll proxy it to Groq
                # For now, let's assume we handle it in AIService
                transcription = await ai_service.transcribe_audio(audio_file, model=requested_model)
                return JsonResponse({"text": transcription} if transcription else {"error": "Transcription failed"})
            return JsonResponse({"error": "Unsupported media type"}, status=415)
        
        if not task:
            return JsonResponse({"error": "Missing task"}, status=400)
            
        prompts = {
            "explain": f"Explain this code concisely:\n\n{code}",
            "debug": f"Find bugs in this code and suggest fixes:\n\n{code}\nContext: {context}",
            "write": f"Write code based on this request:\n\n{context}\n\nexisting code context:\n{code}",
            "autocomplete": f"Continue the following {language} code. Return ONLY the code needed to complete the current line or block, no explanations:\n\n{code}",
            "analyze_data": f"Analyze this dataset sample and return a JSON object with 'summary' (string) and 'suggestions' (list of {{'label': str, 'code': str}} objects for pandas analysis):\n\n{data_sample}"
        }
        
        prompt = prompts.get(task, f"Analyze this:\n{code or context or data_sample}")
        
        # 3.3: Use unified AI service with orchestration support
        ai_service = get_ai_service()
        response = await ai_service.generate_json(prompt, requested_model=requested_model)
        
        if response is None:
            return JsonResponse({"error": "AI service failure"}, status=500)
        
        # If it was an autocomplete task, we should ensure we return a 'code' field even if AI returned raw string
        if task == 'autocomplete' and isinstance(response, dict) and 'code' not in response:
            # Sometime AI returns {"result": "..."} instead of {"code": "..."}
            response['code'] = response.get('result', response.get('text', ''))

        return JsonResponse(response)

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

# --- NEW STUDIO SYNC API (Phase 2) ---

@login_required
@require_POST
def studio_github_sync(request):
    """
    Unified endpoint to Sync Studio with GitHub.
    Handles:
    1. Creating new repos (create_new=True)
    2. Pushing to existing repos
    3. Auto-creating/Updating Kiri Projects
    """
    try:
        data = json.loads(request.body)
        files = data.get('files', {})
        repo_name = data.get('repo_name') # For creation
        repo_full_name = data.get('repo_full_name') # For syncing existing
        description = data.get('description', 'Created with Kiri Studio')
        is_private = data.get('private', False)
        create_new = data.get('create_new', False)
        studio_type = data.get('studio_type', 'py') # 'py' or 'js'

        if not files:
            return JsonResponse({"error": "No files to sync"}, status=400)

        # A. Create New Repo Flow
        if create_new:
            if not repo_name:
                return JsonResponse({"error": "Repository name required"}, status=400)
            
            repo_data, error = GitHubService.create_repository(request.user, repo_name, description, is_private)
            if error:
                return JsonResponse({"error": error}, status=400)
            
            repo_full_name = repo_data['full_name']
            import time
            time.sleep(1)

        # B. Push Code Flow
        if not repo_full_name:
             return JsonResponse({"error": "Target repository not specified"}, status=400)

        result, error = GitHubService.commit_files(request.user, repo_full_name, files)
        if error:
             return JsonResponse({"error": error}, status=400)

        # C. Automatic Platform Project Sync
        github_url = f"https://github.com/{repo_full_name}"
        
        # Decide Lane based on Studio Type
        lane = Project.Lane.PY_STUDIO if studio_type == 'py' else Project.Lane.JS_STUDIO
        
        project, created = Project.objects.update_or_create(
            github_repo_url=github_url,
            defaults={
                'name': repo_name or repo_full_name.split('/')[-1],
                'description': description,
                'submitted_by': request.user,
                'last_synced_at': timezone.now(),
                'lane': lane,
                'is_approved': True
            }
        )

        return JsonResponse({
            "status": "success",
            "repo_url": github_url,
            "project_slug": project.slug,
            "message": "Repository created and Project synced!" if create_new else "Code pushed and Project updated!"
        })

    except Exception as e:
        logger.error(f"Studio Sync Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@require_GET
def studio_proxy_repo(request):
    """
    Proxies a GitHub Repo ZIP download to avoid CORS issues in PyStudio.
    """
    repo_url = request.GET.get('repo')
    if not repo_url:
        return HttpResponse("Missing repo", status=400)
    
    parsed = GitHubService.parse_repo_url(repo_url)
    if not parsed:
        return HttpResponse("Invalid repo URL", status=400)
        
    owner, repo = parsed
    
    # Get user token
    token = None
    integration = request.user.integrations.filter(platform="github").first()
    if integration:
        token = integration.get_decrypted_access_token()
    
    # URL for zipball
    zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/main" # Try main first
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f"token {token}"
        
    try:
        # Stream the response
        r = requests.get(zip_url, headers=headers, stream=True)
        if r.status_code == 404:
             # Try master
             zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/master"
             r = requests.get(zip_url, headers=headers, stream=True)
        
        if r.status_code != 200:
            return HttpResponse(f"GitHub Error: {r.status_code}", status=r.status_code)

        resp = StreamingHttpResponse(r.iter_content(chunk_size=8192), content_type="application/zip")
        resp['Content-Disposition'] = f'attachment; filename="{repo}.zip"'
        return resp
        
    except Exception as e:
        logger.error(f"Proxy Error: {e}")
        return HttpResponse("Proxy Error", status=500)