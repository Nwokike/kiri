import os
import logging
import time
from datetime import timedelta
from django.tasks import task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@task()
def sync_github_stats():
    """
    Syncs stars, forks, and description from GitHub for all projects.
    Uses centralized GitHubService with batching to avoid rate limits.
    """
    from projects.models import Project
    from projects.utils import sync_project_metadata

    logger.info("Starting GitHub stats sync...")

    BATCH_SIZE = 20
    total_projects = Project.objects.count()
    if total_projects == 0:
        return

    num_batches = (total_projects + BATCH_SIZE - 1) // BATCH_SIZE
    current_hour = timezone.now().hour
    current_minute = timezone.now().minute
    batch_index = (current_hour * 2 + (current_minute // 30)) % num_batches
    batch_offset = batch_index * BATCH_SIZE

    projects = Project.objects.all().order_by('id')[batch_offset:batch_offset + BATCH_SIZE]

    updated_count = 0
    errors = 0

    for project in projects:
        try:
            if sync_project_metadata(project):
                logger.info(f"Synced {project.name}")
                updated_count += 1
        except Exception as e:
            logger.error(f"Error syncing {project.name}: {e}")
            errors += 1

    logger.info(f"GitHub Sync Complete. Updated: {updated_count}, Errors: {errors}")


@task()
def cleanup_tmp_files():
    """
    Cleans up temporary files older than 1 hour.
    Uses platform-appropriate temp directory detection.
    """
    import tempfile

    logger.info("Starting temporary file cleanup...")

    temp_dirs = [
        os.path.join(tempfile.gettempdir(), 'kiri_repos'),
        os.path.join(settings.BASE_DIR, 'tmp'),
    ]

    deleted_count = 0
    errors = 0
    now = time.time()
    max_age = 3600  # 1 hour

    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue

        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                filepath = os.path.join(root, name)
                try:
                    if now - os.path.getmtime(filepath) > max_age:
                        os.remove(filepath)
                        deleted_count += 1
                except OSError as e:
                    logger.warning(f"Failed to delete {filepath}: {e}")
                    errors += 1

            for name in dirs:
                dirpath = os.path.join(root, name)
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass

    logger.info(f"Cleanup Complete. Deleted {deleted_count} files. Errors: {errors}")


@task()
def prune_cache_table():
    """Prune expired entries from the database cache to prevent unbounded growth."""
    from django.db import connection

    logger.info("Pruning database cache table...")
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM kiri_cache_table WHERE expires < datetime('now')"
        )
        deleted = cursor.rowcount
    logger.info(f"Cache pruning complete. Removed {deleted} expired entries")


@task()
def sync_publications():
    """
    Fetches all repos with 'kiri-article' topic and creates/updates publications.
    """
    from projects.services import GitHubService
    from publications.models import Publication
    from publications.utils import process_markdown
    from django.utils.text import slugify

    logger.info("Starting Publications sync...")

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Kiri-Research-Labs',
    }
    github_token = os.environ.get('GITHUB_TOKEN', '')
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    # Fetch authenticated user's repos or specify fallback
    try:
        import requests
        if github_token:
            url = "https://api.github.com/user/repos?type=owner&per_page=100"
        else:
            logger.warning("No GITHUB_TOKEN, skipping private/authenticated fetch.")
            return

        page = 1
        updated_count = 0

        while True:
            response = requests.get(f"{url}&page={page}", headers=headers, timeout=15)
            if response.status_code != 200:
                break
            
            repos = response.json()
            if not repos:
                break

            for repo_data in repos:
                topics = repo_data.get('topics', [])
                if 'kiri-article' in topics:
                    repo_name = repo_data['name']
                    owner_login = repo_data['owner']['login']
                    
                    # Fetch README
                    readme_url = f"https://api.github.com/repos/{owner_login}/{repo_name}/readme"
                    readme_resp = requests.get(readme_url, headers=headers, timeout=10)
                    
                    if readme_resp.status_code == 200:
                        import base64
                        readme_json = readme_resp.json()
                        raw_markdown = base64.b64decode(readme_json['content']).decode('utf-8')
                        
                        html_content = process_markdown(owner_login, repo_name, raw_markdown)
                        
                        # Clean title
                        title = repo_data.get('description') or repo_name.replace('-', ' ').title()
                        slug = slugify(repo_name)
                        
                        Publication.objects.update_or_create(
                            repo_name=repo_name,
                            defaults={
                                'title': title,
                                'slug': slug,
                                'description': repo_data.get('description', ''),
                                'html_content': html_content,
                                'github_url': repo_data['html_url'],
                                'topics': ",".join([t for t in topics if t != 'kiri-article']),
                                'published_at': repo_data.get('pushed_at') or repo_data.get('created_at'),
                            }
                        )
                        updated_count += 1

            if len(repos) < 100:
                break
            page += 1

        logger.info(f"Publications Sync Complete. Updated: {updated_count}")

    except Exception as e:
        logger.error(f"Error syncing publications: {e}")
