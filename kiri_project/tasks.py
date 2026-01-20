import os
import datetime
import requests
import hashlib
import time
import logging
from huey.contrib.djhuey import periodic_task, task, HUEY as huey
import boto3
from django.conf import settings
from django.utils import timezone
import shutil

# Configure logging
logger = logging.getLogger(__name__)

# Huey is configured via djhuey settings - HUEY imported above

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
    Uses centralized GitHubService with batching to avoid rate limits.
    """
    from projects.models import Project
    from projects.utils import sync_project_metadata
    
    logger.info("Starting GitHub stats sync...")
    
    # Batch projects to avoid GitHub rate limits (5000/hr)
    # Each 30-min run processes a different batch
    BATCH_SIZE = 20
    current_minute = timezone.now().minute
    batch_offset = (current_minute // 30) * BATCH_SIZE
    
    total_projects = Project.objects.count()
    projects = Project.objects.all()[batch_offset:batch_offset + BATCH_SIZE]
    
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
def classify_project_lane(project_id: int):
    """
    Background task to classify a project and generate execution config.
    Called when a project is submitted or when user triggers re-classification.
    
    Uses AI (Gemini + Groq fallback) to analyze the repository and determine:
    - Lane A: Client-side (WebContainer) - React, Vue, Node.js
    - Lane B: Cloud Container (Binder) - Django, Flask, FastAPI
    - Lane C: GPU Cluster (Colab) - PyTorch, TensorFlow, Transformers
    """
    from projects.models import Project
    from projects.gist_service import GistService
    from core.ai_service import AIService
    
    logger.info(f"Starting lane classification for project {project_id}")
    
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error(f"Project {project_id} not found")
        return
    
    # 1. Fetch repository structure from GitHub
    from projects.services import GitHubService
    repo_files = GitHubService.fetch_structure(project.github_repo_url)
    
    if not repo_files:
        logger.error(f"Failed to fetch repo structure for {project.github_repo_url}")
        project.lane = 'P'  # Keep as pending
        project.lane_classification_reason = "Failed to fetch repository structure"
        project.save()
        return
    
    # 2. AI Classification (Gemini + Groq fallback)
    result = AIService.classify_repository_lane(repo_files)
    
    # 3. Save classification result
    project.lane = result['lane']
    project.lane_classification_reason = result.get('reason', '')
    project.start_command = result.get('start_command', '')
    
    # 4. Generate magic link for Lanes B and C
    if project.lane == 'B':
        gist_id = GistService.create_binder_gist(project)
        if gist_id:
            project.gist_id = gist_id
            project.execution_url = GistService.build_binder_url(
                gist_id, 
                port=8000 if 'django' in result.get('reason', '').lower() else 5000
            )
            logger.info(f"Created Binder execution URL for project {project_id}")
        else:
            logger.warning(f"Failed to create Binder gist for project {project_id}")
    
    elif project.lane == 'C':
        notebook_json = AIService.generate_colab_notebook(
            project.github_repo_url,
            project.start_command
        )
        gist_id = GistService.create_colab_gist(project, notebook_json)
        if gist_id:
            project.gist_id = gist_id
            project.execution_url = GistService.build_colab_url(gist_id)
            logger.info(f"Created Colab execution URL for project {project_id}")
        else:
            logger.warning(f"Failed to create Colab gist for project {project_id}")
    
    # Lane A doesn't need server-side prep (runs in browser)
    
    project.save()
    logger.info(f"Classified project {project_id} as Lane {project.lane}: {project.lane_classification_reason}")


@task()
def sync_github_star(favorite_id: int):
    """
    Background task to star a GitHub repository when user likes a project on Kiri.
    Only runs if user has granted public_repo scope.
    """
    from core.models import Favorite
    from users.models import UserIntegration
    from projects.models import Project
    from django.contrib.contenttypes.models import ContentType
    
    logger.info(f"Starting GitHub star sync for favorite {favorite_id}")
    
    try:
        favorite = Favorite.objects.select_related('user').get(id=favorite_id)
    except Favorite.DoesNotExist:
        logger.error(f"Favorite {favorite_id} not found")
        return
    
    # Check if the favorited item is a Project
    project_ct = ContentType.objects.get_for_model(Project)
    if favorite.content_type_id != project_ct.id:
        logger.info(f"Favorite {favorite_id} is not a project, skipping star sync")
        return
    
    # Get the project
    try:
        project = Project.objects.get(id=favorite.object_id)
    except Project.DoesNotExist:
        logger.error(f"Project {favorite.object_id} not found")
        return
    
    # Check if project has a GitHub URL
    if not project.github_repo_url:
        logger.info(f"Project {project.id} has no GitHub URL, skipping star sync")
        return
    
    # Check if user has GitHub integration with repo scope
    try:
        github_integration = UserIntegration.objects.get(
            user=favorite.user,
            platform='github',
            has_repo_scope=True
        )
    except UserIntegration.DoesNotExist:
        logger.info(f"User {favorite.user.id} has no GitHub integration with repo scope")
        return
    
    # Parse repo URL
    from projects.services import GitHubService
    parsed = GitHubService.parse_repo_url(project.github_repo_url)
    if not parsed:
        logger.error(f"Failed to parse GitHub URL: {project.github_repo_url}")
        return
    
    owner, repo = parsed
    
    # Star the repository
    try:
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {github_integration.access_token}'
        }
        
        response = requests.put(
            f"https://api.github.com/user/starred/{owner}/{repo}",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 204:
            # Success - mark as synced
            favorite.github_synced = True
            favorite.sync_failed = False
            favorite.save(update_fields=['github_synced', 'sync_failed'])
            logger.info(f"Successfully starred {owner}/{repo} for user {favorite.user.username}")
        elif response.status_code == 401:
            # Token expired or invalid
            logger.error(f"GitHub token invalid for user {favorite.user.id}")
            favorite.sync_failed = True
            favorite.save(update_fields=['sync_failed'])
        else:
            logger.error(f"Failed to star repo: {response.status_code} - {response.text}")
            favorite.sync_failed = True
            favorite.save(update_fields=['sync_failed'])
            
    except Exception as e:
        logger.error(f"Error starring repo: {e}")
        favorite.sync_failed = True
        favorite.save(update_fields=['sync_failed'])


@task()
def create_notification(recipient_id: int, notification_type: str, title: str, 
                       message: str = '', link: str = '', actor_id: int = None,
                       content_type_id: int = None, object_id: int = None):
    """
    Background task to create a notification for a user.
    """
    from core.models import Notification
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        logger.error(f"Recipient {recipient_id} not found")
        return
    
    actor = None
    if actor_id:
        try:
            actor = User.objects.get(id=actor_id)
        except User.DoesNotExist:
            pass
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        actor=actor,
        content_type_id=content_type_id,
        object_id=object_id,
    )
    
    logger.info(f"Created notification {notification.id} for user {recipient.username}")
    return notification.id


@task()
def analyze_project_task(project_id: int):
    """
    Background task to analyze a project using AI Advisor.
    Wrapper for async service function.
    """
    import asyncio
    from projects.ai_advisor import analyze_project
    
    logger.info(f"Starting AI analysis for project {project_id}")
    
    # Run async function in sync task
    try:
        # Use asyncio.run for a fresh event loop in the worker process
        result = asyncio.run(analyze_project(project_id))
        if result:
            logger.info(f"AI Analysis task completed for project {project_id}")
        else:
            logger.warning(f"AI Analysis task failed/returned None for project {project_id}")
    except Exception as e:
        logger.error(f"Error in analyze_project_task: {e}")
        # Log to ErrorLog
        from core.models import ErrorLog
        try:
            # Sync creation for ErrorLog inside sync wrapper
            ErrorLog.objects.create(
                level='error',
                path='kiri_project.tasks.analyze_project_task',
                message=str(e),
                exception_type=type(e).__name__
            )
        except Exception:
            pass


@periodic_task(huey.crontab(minute=0, hour='*/4'))  # Run every 4 hours
def cleanup_tmp_files():
    """
    Cleans up temporary files to maintain the "Zero-Local-File" policy.
    Removes files in /tmp/kiri/ older than 1 hour.
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
