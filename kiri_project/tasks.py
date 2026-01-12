import os
import datetime
import requests
from huey import SqliteHuey
from huey.contrib.djhuey import periodic_task, task
import boto3
from django.conf import settings
from django.utils import timezone
import shutil

# Configure Huey with SQLite backend
huey = SqliteHuey(filename=str(settings.BASE_DIR / 'db.sqlite3'))

@task()
def update_project_hot_status():
    """
    Updates the 'is_hot' status of projects based on view counts.
    Simple logic: Top 10% of projects by views + stars are marked HOT.
    """
    from projects.models import Project
    from django.db.models import F
    
    # Reset all
    Project.objects.update(is_hot=False)
    
    # Calculate score = views + (stars * 10)
    # This is a naive implementation, can be complexified later
    projects = Project.objects.annotate(
        score=F('view_count') + (F('stars_count') * 10)
    ).order_by('-score')
    
    # Mark top 5 as HOT
    top_projects = projects[:5]
    for p in top_projects:
        p.is_hot = True
        p.save()
    
    print(f"Updated HOT projects at {timezone.now()}")

@periodic_task(huey.crontab(hour=3, minute=0)) # Run at 3 AM daily
def backup_db_to_r2():
    """
    Backups the SQLite database to Cloudflare R2 daily.
    Keeps only the last 3 backups to save space.
    """
    print("Starting daily database backup...")
    
    db_path = settings.BASE_DIR / 'db.sqlite3'
    if not db_path.exists():
        print("Database file not found!")
        return

    # 1. Upload new backup
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}.sqlite3"
    
    s3 = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name='auto' 
    )
    
    try:
        with open(db_path, 'rb') as f:
            s3.upload_fileobj(f, settings.AWS_STORAGE_BUCKET_NAME, f"backups/{backup_name}")
        print(f"Uploaded {backup_name} to R2.")
    except Exception as e:
        print(f"Failed to upload backup: {e}")
        return

    # 2. Cleanup old backups (Keep last 3)
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
                print(f"Deleted {num_to_delete} old backups.")
            
    except Exception as e:
        print(f"Failed to cleanup old backups: {e}")

@periodic_task(huey.crontab(minute='*/30')) # Run every 30 mins
def sync_github_stats():
    """
    Syncs stars, forks, and description from GitHub for all projects.
    """
    from projects.models import Project
    print("Starting GitHub stats sync...")
    projects = Project.objects.all()
    
    headers = {}
    if settings.SOCIALACCOUNT_PROVIDERS['github']['APP']['client_id']:
         # In a real scenario, use an installation token or Oauth token if available. 
         # For public repos, unauthenticated is fine but rate limited (60/hr).
         pass

    for project in projects:
        if not project.github_repo_url or 'github.com' not in project.github_repo_url:
            continue
            
        try:
            # Extract owner/repo
            parts = project.github_repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                project.stars_count = data.get('stargazers_count', 0)
                project.forks_count = data.get('forks_count', 0)
                project.language = data.get('language') or ''
                # Only update description if it was previously empty (assume manual edits are preferred)
                if not project.description: 
                    project.description = data.get('description') or ''
                
                # Sync topics
                if not project.topics:
                    project.topics = data.get('topics', [])
                
                project.last_synced_at = timezone.now()
                project.save(update_fields=['stars_count', 'forks_count', 'language', 'description', 'topics', 'last_synced_at'])
                print(f"Synced {project.name}: {project.stars_count} stars")
            else:
                print(f"Failed to sync {project.name}: {response.status_code}")
                
        except Exception as e:
            print(f"Error syncing {project.name}: {e}")
