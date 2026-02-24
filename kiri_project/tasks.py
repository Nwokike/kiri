import os
import requests
import hashlib
import time
import logging
from django.tasks import task

from django.conf import settings
from django.utils import timezone

# Configure logging
logger = logging.getLogger(__name__)

# Native tasks configured via settings.TASKS

def calculate_file_md5(filepath):
    """Calculates MD5 hash of a file efficiently."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

@task()
def update_project_hot_status():
    """
    Updates the 'is_hot' status of projects based on view counts.
    Simple logic: Top 10% of projects by views + stars are marked HOT.
    """
    from projects.models import Project
    from django.db.models import F
    
    logger.info("Starting HOT projects update...")
    
    # Reset all
    Project.objects.update(is_hot=False)
    
    # Calculate score = views + (stars * 10)
    projects = Project.objects.annotate(
        score=F('view_count') + (F('stars_count') * 10)
    ).order_by('-score')
    
    # Mark top 5 as HOT using bulk_update to avoid N+1
    top_project_ids = list(projects[:5].values_list('id', flat=True))
    updated_count = Project.objects.filter(id__in=top_project_ids).update(is_hot=True)
    
    logger.info(f"Updated {updated_count} projects to HOT at {timezone.now()}")

@task()
def sync_github_stats():
    """
    Syncs stars, forks, and description from GitHub for all projects.
    Uses centralized GitHubService with batching to avoid rate limits.
    """
    from projects.models import Project
    from projects.utils import sync_project_metadata
    
    logger.info("Starting GitHub stats sync...")
    
    # Batch projects to avoid GitHub rate limits (5000/hr)
    # 4.1: Adjust batch offset logic to rotate through all projects
    BATCH_SIZE = 20
    total_projects = Project.objects.count()
    if total_projects == 0:
        return
        
    num_batches = (total_projects + BATCH_SIZE - 1) // BATCH_SIZE
    current_hour = timezone.now().hour
    current_minute = timezone.now().minute
    # Rotates 48 times a day (every 30 mins)
    batch_index = (current_hour * 2 + (current_minute // 30)) % num_batches
    batch_offset = batch_index * BATCH_SIZE
    
    projects = Project.objects.all().order_by('id')[batch_offset:batch_offset + BATCH_SIZE]
    
    updated_count = 0
    errors = 0
    
    for project in projects:
        try:
            # Reuses the logic we just refactored in utils.py which uses GitHubService
            # This handles caching, parsing, rate limits, and field updates uniformly.
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
    Cleans up temporary files to maintain the "Zero-Local-File" policy.
    Removes files in /tmp/kiri_repos, C:\\Windows\\Temp\\kiri, and BASE_DIR/tmp older than 1 hour.
    """
    import time
    
    logger.info("Starting temporary file cleanup...")
    
    # Define temp directories to clean
    # We primarily use /tmp on Linux/Mac, or GetTempPath on Windows
    # For Kiri, we assume a designated temp workspace might be used for git clones
    temp_dirs = [
        '/tmp/kiri_repos',          # Linux/Container default
        'C:\\Windows\\Temp\\kiri',  # Windows potential path
        os.path.join(settings.BASE_DIR, 'tmp'), # Project local tmp
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
                    # Check age
                    if now - os.path.getmtime(filepath) > max_age:
                        os.remove(filepath)
                        deleted_count += 1
                except Exception as e:
                    errors += 1
            
            for name in dirs:
                dirpath = os.path.join(root, name)
                try:
                    # Try to remove empty dirs
                    os.rmdir(dirpath)
                except:
                    pass
    
    logger.info(f"Cleanup Complete. Deleted {deleted_count} files. Errors: {errors}")


@task()
def backup_db_to_r2():
    """No-op stub — backup not configured for this platform."""
    logger.info("backup_db_to_r2 called (no-op)")


@task()
def dummy_task(a: int = 0, b: int = 0) -> int:
    """
    Simple no-op task for testing the task framework.
    Returns the sum of a and b.
    """
    result = a + b
    logger.info("dummy_task called with a=%d, b=%d, result=%d", a, b, result)
    return result
