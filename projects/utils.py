from django.utils import timezone
from datetime import timedelta
from .services import GitHubService


def sync_project_metadata(project):
    """
    Updates a Project instance with data from GitHub.
    Returns True if updated, False otherwise.
    """
    if project.last_synced_at and timezone.now() - project.last_synced_at < timedelta(hours=1):
        return False

    data = GitHubService.fetch_repo_data(project.github_repo_url)
    if data:
        project.stars_count = data['stars_count']
        project.forks_count = data['forks_count']
        project.language = data['language'] or ''

        if not project.description:
            project.description = data['description'] or ''

        if not project.topics and data.get('topics'):
            # Convert list to comma-separated string
            topics = data['topics']
            if isinstance(topics, list):
                project.topics = ', '.join(topics)
            else:
                project.topics = str(topics)

        project.last_synced_at = timezone.now()
        project.save(update_fields=[
            'stars_count', 'forks_count', 'language',
            'description', 'topics', 'last_synced_at',
        ])
        return True
    return False
