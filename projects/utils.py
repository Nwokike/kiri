from django.utils import timezone
from datetime import timedelta
from .services import GitHubService

def fetch_github_metadata(repo_url):
    """
    Deprecated wrapper: Use GitHubService.fetch_repo_data directly.
    Kept for backward compatibility if needed, but returns subset of data to match old signature.
    """
    data = GitHubService.fetch_repo_data(repo_url)
    if data:
        return {
            'stars_count': data['stars_count'],
            'language': data['language'],
            'description': data['description']
        }
    return None

def sync_project_metadata(project):
    """
    Updates a Project instance with data from GitHub.
    Returns True if updated, False otherwise.
    """
    # Rate limit check: Don't sync if synced in last hour
    if project.last_synced_at and timezone.now() - project.last_synced_at < timedelta(hours=1):
        return False

    data = GitHubService.fetch_repo_data(project.github_repo_url)
    if data:
        project.stars_count = data['stars_count']
        project.forks_count = data['forks_count']
        project.language = data['language']
        
        # Optional: Update description if empty
        if not project.description:
            project.description = data['description']
            
        # Update topics
        if not project.topics and data['topics']:
            project.topics = data['topics']
        
        project.last_synced_at = timezone.now()
        # Save all potentially changed fields
        project.save(update_fields=['stars_count', 'forks_count', 'language', 'description', 'topics', 'last_synced_at'])
        return True
    return False
