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
