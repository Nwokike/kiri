import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def fetch_github_metadata(repo_url):
    """
    Fetches metadata from GitHub API for a given repository URL.
    Returns a dict with 'stars_count', 'language', 'description' (optional).
    """
    if 'github.com' not in repo_url:
        return None

    try:
        # Extract owner and repo name
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        # Use GITHUB_TOKEN if available to avoid rate limits
        # github_token = os.environ.get('GITHUB_TOKEN')
        # if github_token:
        #     headers['Authorization'] = f'token {github_token}'

        response = requests.get(api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'stars_count': data.get('stargazers_count', 0),
                'language': data.get('language', 'Unknown'),
                'description': data.get('description', ''),
            }
    except Exception as e:
        print(f"Error fetching GitHub data: {e}")
        return None
    
    return None

def sync_project_metadata(project):
    """
    Updates a Project instance with data from GitHub.
    """
    # Rate limit check: Don't sync if synced in last hour
    if project.last_synced_at and timezone.now() - project.last_synced_at < timedelta(hours=1):
        return False

    metadata = fetch_github_metadata(project.github_repo_url)
    if metadata:
        project.stars_count = metadata['stars_count']
        project.language = metadata['language'] or 'Unknown'
        # Optional: Update description if empty
        if not project.description:
            project.description = metadata.get('description', '')
        
        project.last_synced_at = timezone.now()
        project.save(update_fields=['stars_count', 'language', 'description', 'last_synced_at'])
        return True
    return False
