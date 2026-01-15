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
    repo_files = fetch_github_structure(project.github_repo_url)
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


def fetch_github_structure(repo_url: str) -> dict:
    """
    Fetches repository structure and key files from GitHub for lane classification.
    
    Returns:
        Dict with comprehensive repo info for AI analysis:
        - file_list: List of file paths in the repo
        - package_json: contents of package.json (Node.js)
        - requirements_txt: contents of requirements.txt (Python)
        - pyproject_toml: contents of pyproject.toml (Python)
        - dockerfile: contents of Dockerfile (Docker)
        - main_file: contents of main entry point (app.py, main.py, etc.)
        - readme: first 1000 chars of README for context
    """
    from projects.services import GitHubService
    
    parsed = GitHubService.parse_repo_url(repo_url)
    if not parsed:
        return None
    
    owner, repo = parsed
    
    result = {
        'file_list': [],
        'package_json': '',
        'requirements_txt': '',
        'pyproject_toml': '',
        'dockerfile': '',
        'main_file': '',
        'readme': ''
    }
    
    # Get file tree (first 100 files)
    try:
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = f'token {token}'
        
        response = requests.get(tree_url, headers=headers, timeout=15)
        if response.status_code == 200:
            tree = response.json().get('tree', [])
            result['file_list'] = [item['path'] for item in tree[:150] if item['type'] == 'blob']
    except Exception as e:
        logger.warning(f"Failed to fetch file tree: {e}")
    
    def fetch_file(filepath: str, limit: int = 2000) -> str:
        """Helper to fetch a single file from the repo."""
        try:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{filepath}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.text[:limit]
        except Exception:
            pass
        return ''
    
    # Fetch key dependency/config files
    result['package_json'] = fetch_file('package.json')
    result['requirements_txt'] = fetch_file('requirements.txt')
    result['pyproject_toml'] = fetch_file('pyproject.toml')
    result['dockerfile'] = fetch_file('Dockerfile', limit=1500)
    
    # Try to find and fetch main entry point
    entry_points = ['app.py', 'main.py', 'run.py', 'server.py', 'manage.py', 'index.js', 'src/index.js', 'src/main.py']
    for entry in entry_points:
        if entry in result['file_list'] or f'src/{entry}' in result['file_list']:
            content = fetch_file(entry, limit=1000)
            if content:
                result['main_file'] = content
                break
    
    # Fetch README for additional context
    for readme_name in ['README.md', 'readme.md', 'README.rst', 'README']:
        readme = fetch_file(readme_name, limit=1000)
        if readme:
            result['readme'] = readme
            break
    
    return result

