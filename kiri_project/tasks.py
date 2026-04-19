import os
import logging
import time
import requests
from huey.contrib.djhuey import db_task, db_periodic_task
from huey import crontab
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute='0', hour='*'))
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


@db_periodic_task(crontab(minute='0', hour='1'))
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


@db_periodic_task(crontab(minute='0', hour='3'))
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


@db_periodic_task(crontab(minute='30'))
def sync_publications():
    """
    Fetches all repositories from the 'kiri-labs' organization and syncs them as publications.
    """
    from publications.models import Publication
    from publications.utils import process_markdown

    logger.info("Starting Publications sync for Organization: kiri-labs...")

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Kiri-Research-Labs',
    }
    github_token = os.environ.get('GITHUB_TOKEN', '')
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    try:
        page = 1
        updated_count = 0
        synced_repos = []

        while True:
            # Fetch all repos (including private/internal if token allows)
            url = f"https://api.github.com/orgs/kiri-labs/repos?per_page=100&page={page}&type=all"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"GitHub API Error: {response.status_code} - {response.text}")
                break
            
            repos = response.json()
            if not repos or not isinstance(repos, list):
                break

            for repo_data in repos:
                repo_name = repo_data['name']
                owner_login = repo_data['owner']['login']
                
                # Fetch README content
                readme_url = f"https://api.github.com/repos/{owner_login}/{repo_name}/readme"
                readme_resp = requests.get(readme_url, headers=headers, timeout=10)
                
                html_content = ""
                if readme_resp.status_code == 200:
                    import base64
                    readme_json = readme_resp.json()
                    raw_markdown = base64.b64decode(readme_json['content']).decode('utf-8')
                    default_branch = repo_data.get('default_branch', 'main')
                    html_content = process_markdown(owner_login, repo_name, default_branch, raw_markdown)
                
                # Metadata extraction
                title_str = repo_name.replace('-', ' ').title()
                slug = slugify(repo_name)
                description = repo_data.get('description', '') or "Research publication by Kiri Research Labs."
                topics = ",".join(repo_data.get('topics', []))
                published_at = repo_data.get('pushed_at') or repo_data.get('created_at')

                pub, created = Publication.objects.update_or_create(
                    repo_name=repo_name,
                    defaults={
                        'title': title_str,
                        'slug': slug,
                        'description': description,
                        'html_content': html_content,
                        'github_url': repo_data['html_url'],
                        'topics': topics,
                        'published_at': published_at,
                        'last_synced_at': timezone.now()
                    }
                )

                synced_repos.append(repo_name)
                updated_count += 1
                
                if created:
                    try:
                        post_to_facebook('publication', pub.id)
                    except Exception as fb_err:
                        logger.error(f"Failed to queue FB post for {repo_name}: {fb_err}")

            if len(repos) < 100:
                break
            page += 1

        # Pruning: Delete local publications that are no longer in the organization repos
        deleted_count = 0
        if synced_repos:
            stale_entries = Publication.objects.exclude(repo_name__in=synced_repos)
            deleted_count = stale_entries.count()
            stale_entries.delete()

        logger.info(f"Publications Sync Complete. Updated: {updated_count}. Deleted: {deleted_count}")

    except Exception as e:
        logger.error(f"Critical error in publications sync: {e}")


@db_task()
def post_to_facebook(content_type, object_id):
    """
    Unified task to post a Publication or Project to Facebook.
    Uses Bearer tokens and includes both platform and source URLs.
    """
    from django.urls import reverse
    from publications.models import Publication
    from projects.models import Project
    
    try:
        if content_type == 'publication':
            obj = Publication.objects.get(id=object_id)
            source_url = obj.github_url
            path = reverse('publications:detail', kwargs={'slug': obj.slug})
        elif content_type == 'project':
            obj = Project.objects.get(id=object_id)
            source_url = obj.github_repo_url or obj.huggingface_url
            path = reverse('projects:detail', kwargs={'slug': obj.slug})
        else:
            return

        # Base site URL - using a fallback for local testing if not in settings
        site_url = getattr(settings, 'SITE_URL', 'https://kiri.ng').rstrip('/')
        full_platform_url = f"{site_url}{path}"
        
        page_id = os.environ.get('META_PAGE_ID')
        access_token = os.environ.get('LONG_META_PAGE_TOKEN')
        
        if not page_id or not access_token:
            logger.warning("Meta credentials missing. Skipping FB post.")
            return

        url = f"https://graph.facebook.com/v20.0/{page_id}/feed"
        message = (
            f"🚀 Newly Published: {obj.title}\n\n"
            f"{obj.description}\n\n"
            f"🔗 View on Kiri: {full_platform_url}\n"
            f"📦 Source Code: {source_url}"
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        payload = {"message": message}
        
        response = requests.post(url, headers=headers, data=payload, timeout=12)
        
        if response.status_code != 200:
            logger.error(f"Facebook API failed: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        logger.info(f"Successfully posted {content_type} '{obj.title}' to Facebook.")
        
    except (Publication.DoesNotExist, Project.DoesNotExist):
        logger.error(f"{content_type} {object_id} missing for FB post.")
    except Exception as e:
        logger.error(f"Facebook task error: {e}")

