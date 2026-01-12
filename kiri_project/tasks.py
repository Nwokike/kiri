import os
import datetime
import requests
import hashlib
import time
import logging
from huey import SqliteHuey
from huey.contrib.djhuey import periodic_task, task
import boto3
from django.conf import settings
from django.utils import timezone
import shutil

# Configure logging
logger = logging.getLogger(__name__)

# Configure Huey with SQLite backend
huey = SqliteHuey(filename=settings.HUEY['filename'])

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
    
    # Mark top 5 as HOT
    updated_count = 0
    top_projects = projects[:5]
    for p in top_projects:
        p.is_hot = True
        p.save()
        updated_count += 1
    
    logger.info(f"Updated {updated_count} projects to HOT at {timezone.now()}")

@periodic_task(huey.crontab(hour=3, minute=0)) # Run at 3 AM daily
def backup_db_to_r2():
    """
    Backups the SQLite database to Cloudflare R2 daily with verification.
    Keeps only the last 3 backups to save space.
    """
    logger.info("Starting daily database backup...")
    
    db_path = settings.BASE_DIR / 'db.sqlite3'
    if not db_path.exists():
        logger.error("Database file not found!")
        return

    # 1. Prepare backup
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}.sqlite3"
    
    # Calculate checksum before upload
    local_md5 = calculate_file_md5(db_path)
    logger.info(f"Local database MD5: {local_md5}")
    
    s3 = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name='auto' 
    )
    
    try:
        # Upload with standard S3/R2 put_object behavior
        with open(db_path, 'rb') as f:
            s3.upload_fileobj(
                f, 
                settings.AWS_STORAGE_BUCKET_NAME, 
                f"backups/{backup_name}",
                ExtraArgs={'ContentType': 'application/x-sqlite3'}
            )
        
        # 2. Verify Upload
        metadata = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"backups/{backup_name}")
        remote_etag = metadata.get('ETag', '').strip('"')
        
        if remote_etag == local_md5:
            logger.info(f"Backup {backup_name} verified successfully (ETag match).")
        else:
            logger.error(f"Backup verification FAILED for {backup_name}. Local: {local_md5}, Remote: {remote_etag}")
            # Optional: Delete corrupted backup or alert admin
            return

    except Exception as e:
        logger.error(f"Failed to upload backup: {e}")
        return

    # 3. Cleanup old backups (Keep last 3)
    try:
        response = s3.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Prefix='backups/'
        )
        
        if 'Contents' in response:
            # Sort by LastModified
            backups = sorted(response['Contents'], key=lambda x: x['LastModified'])
            
            # If more than 3, delete oldest
            if len(backups) > 3:
                num_to_delete = len(backups) - 3
                to_delete = backups[:num_to_delete]
                
                objects_to_delete = [{'Key': obj['Key']} for obj in to_delete]
                
                s3.delete_objects(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Delete={
                        'Objects': objects_to_delete,
                        'Quiet': True
                    }
                )
                logger.info(f"Deleted {num_to_delete} old backups.")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}")

@periodic_task(huey.crontab(minute='*/30')) # Run every 30 mins
def sync_github_stats():
    """
    Syncs stars, forks, and description from GitHub for all projects.
    Uses centralized GitHubService.
    """
    from projects.models import Project
    from projects.utils import sync_project_metadata
    
    logger.info("Starting GitHub stats sync...")
    projects = Project.objects.all()
    
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
