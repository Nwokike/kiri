import re
import requests
import time
from urllib.parse import urlparse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class GitHubService:
    """
    Centralized service for GitHub interactions.
    Handles URL parsing, API fetching, caching, and rate limiting.
    """
    
    BASE_API_URL = "https://api.github.com/repos"
    
    @staticmethod
    def parse_repo_url(url):
        """
        Parses a GitHub URL and returns (owner, repo_name).
        """
        if not url:
            return None
            
        clean_url = url.strip()
        
        # Handle SSH style
        ssh_match = re.match(r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$', clean_url)
        if ssh_match:
            return ssh_match.groups()
            
        # Handle HTTPS style
        try:
            parsed = urlparse(clean_url)
            if 'github.com' not in parsed.netloc:
                return None
                
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[0]
                # Remove .git suffix if present
                repo = path_parts[1]
                if repo.endswith('.git'):
                    repo = repo[:-4]
                return (owner, repo)
        except Exception:
            return None
            
        return None

    @classmethod
    def fetch_repo_data(cls, repo_url):
        """
        Fetches metadata for a repo.
        """
        parsed = cls.parse_repo_url(repo_url)
        if not parsed:
            return None
            
        owner, repo = parsed
        cache_key = f"github_meta_{owner}_{repo}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        api_url = f"{cls.BASE_API_URL}/{owner}/{repo}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Kiri-Research-Labs-Bot'
        }
            
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code in [403, 429]:
                logger.warning(f"GitHub Rate Limit Hit.")
                return None
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'stars_count': data.get('stargazers_count', 0),
                    'forks_count': data.get('forks_count', 0),
                    'language': data.get('language') or 'Unknown',
                    'description': data.get('description', ''),
                    'topics': data.get('topics', []),
                    'last_updated': timezone.now().isoformat()
                }
                cache.set(cache_key, result, 3600)
                return result
                
        except Exception as e:
            logger.error(f"GitHub API Error for {repo_url}: {e}")
            return None
            
        return None

    @classmethod
    def fetch_raw_file(cls, owner: str, repo: str, path: str, limit: int = 40000) -> str:
        """
        Fetches the raw content of a file from GitHub.
        """
        cache_key = f"github_raw_{owner}_{repo}_{hashlib.sha256(path.encode()).hexdigest()}"
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
            
        try:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
            headers = {'User-Agent': 'Kiri-Research-Labs-Bot'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.text[:limit]
                cache.set(cache_key, content, 300)
                return content
        except Exception as e:
            logger.error(f"Error fetching raw file {path}: {e}")
            
        return ''

    @classmethod
    def fetch_structure(cls, repo_url):
        """
        Fetches repository structure and key files.
        """
        parsed = cls.parse_repo_url(repo_url)
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
        
        try:
            tree_url = f"{cls.BASE_API_URL}/{owner}/{repo}/git/trees/HEAD?recursive=1"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(tree_url, headers=headers, timeout=15)
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                result['file_list'] = [item['path'] for item in tree[:150] if item['type'] == 'blob']
        except Exception as e:
            logger.warning(f"Failed to fetch file tree: {e}")
        
        def fetch_file(filepath: str, limit: int = 4000) -> str:
            try:
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{filepath}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    return resp.text[:limit]
            except Exception:
                pass
            return ''
        
        result['package_json'] = fetch_file('package.json')
        result['requirements_txt'] = fetch_file('requirements.txt')
        result['pyproject_toml'] = fetch_file('pyproject.toml')
        result['dockerfile'] = fetch_file('Dockerfile', limit=2000)
        
        entry_points = ['app.py', 'main.py', 'run.py', 'server.py', 'manage.py', 'index.js', 'src/index.js', 'src/main.py']
        for entry in entry_points:
            if entry in result['file_list'] or f'src/{entry}' in result['file_list']:
                content = fetch_file(entry, limit=2000)
                if content:
                    result['main_file'] = content
                    break
        
        result['readme'] = fetch_file('README.md', limit=5000)
        return result

    # --- NEW WRITE CAPABILITIES (Phase 2) ---

    @classmethod
    def create_repository(cls, user, name, description, private=False):
        """
        Creates a new repository for the user.
        Returns: (repo_data, error_message)
        """
        try:
            # Get user's token
            integration = user.integrations.filter(platform="github").first()
            if not integration:
                return None, "GitHub account not connected."

            token = integration.get_decrypted_access_token()
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True  # Create with README so we can commit immediately
            }
            
            resp = requests.post("https://api.github.com/user/repos", json=payload, headers=headers)
            
            if resp.status_code == 201:
                return resp.json(), None
            elif resp.status_code == 422:
                return None, "Repository name already exists."
            else:
                return None, f"GitHub Error: {resp.status_code}"
        except Exception as e:
            logger.error(f"Create Repo Error: {e}")
            return None, str(e)

    @classmethod
    def commit_files(cls, user, repo_full_name, files, commit_message="Update from Kiri Studio"):
        """
        Commits multiple files to a repo using the Git Tree API.
        files: dict of {'filename': 'content'}
        """
        try:
            integration = user.integrations.filter(platform="github").first()
            if not integration:
                return None, "GitHub not connected"
            
            token = integration.get_decrypted_access_token()
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            base_url = f"https://api.github.com/repos/{repo_full_name}"

            # 1. Get reference to HEAD
            ref_resp = requests.get(f"{base_url}/git/ref/heads/main", headers=headers)
            if ref_resp.status_code != 200:
                ref_resp = requests.get(f"{base_url}/git/ref/heads/master", headers=headers)
            
            if ref_resp.status_code != 200:
                # If fresh empty repo, getting ref might fail. 
                # But we used auto_init=True, so main should exist.
                return None, "Could not find branch (main/master)"
            
            latest_commit_sha = ref_resp.json()["object"]["sha"]

            # 2. Create Blobs (Files)
            tree_items = []
            for filename, content in files.items():
                blob_resp = requests.post(f"{base_url}/git/blobs", json={
                    "content": content,
                    "encoding": "utf-8"
                }, headers=headers)
                
                if blob_resp.status_code == 201:
                    tree_items.append({
                        "path": filename,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_resp.json()["sha"]
                    })
            
            # 3. Create Tree
            tree_resp = requests.post(f"{base_url}/git/trees", json={
                "base_tree": latest_commit_sha,
                "tree": tree_items
            }, headers=headers)
            
            if tree_resp.status_code != 201:
                return None, "Failed to create git tree"
                
            new_tree_sha = tree_resp.json()["sha"]

            # 4. Create Commit
            commit_resp = requests.post(f"{base_url}/git/commits", json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [latest_commit_sha]
            }, headers=headers)
            
            if commit_resp.status_code != 201:
                return None, "Failed to create commit"
                
            new_commit_sha = commit_resp.json()["sha"]

            # 5. Update Reference (Push)
            branch_ref = ref_resp.json()['ref'].replace('refs/', '')
            
            push_resp = requests.patch(f"{base_url}/git/refs/{branch_ref}", json={
                "sha": new_commit_sha
            }, headers=headers)
            
            if push_resp.status_code == 200:
                return push_resp.json(), None
            else:
                return None, "Failed to push commit"

        except Exception as e:
            logger.error(f"Commit Error: {e}")
            return None, str(e)