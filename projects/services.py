import re
import requests
import time
from urllib.parse import urlparse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

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
        Handles various formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        
        Returns None if invalid.
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
        Returns dict with keys: stars_count, forks_count, language, description, topics.
        Uses caching to prevent abusing API limits.
        """
        parsed = cls.parse_repo_url(repo_url)
        if not parsed:
            return None
            
        owner, repo = parsed
        
        # Cache Check (1 hour cache)
        cache_key = f"github_meta_{owner}_{repo}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        api_url = f"{cls.BASE_API_URL}/{owner}/{repo}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Kiri-Research-Labs-Bot'
        }
        # Note: Public repos don't need auth. For user-specific actions,
        # pass user's OAuth token from UserIntegration model.
            
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            
            # Rate Limit Handling
            if response.status_code in [403, 429]:
                remaining = response.headers.get('X-RateLimit-Remaining')
                if remaining == '0':
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_sec = max(reset_time - time.time(), 0)
                    logger.warning(f"GitHub Rate Limit Hit. Reset in {wait_sec}s")
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
                
                # Cache successful result
                cache.set(cache_key, result, 3600)
                return result
                
        except Exception as e:
            logger.error(f"GitHub API Error for {repo_url}: {e}")
            return None
            
        return None

    @classmethod
    def fetch_structure(cls, repo_url):
        """
        Fetches repository structure and key files from GitHub.
        
        Returns:
            Dict with comprehensive repo info for AI analysis:
            - file_list: List of file paths in the repo
            - package_json: contents of package.json (Node.js)
            - requirements_txt: contents of requirements.txt (Python)
            - pyproject_toml: contents of pyproject.toml (Python)
            - dockerfile: contents of Dockerfile (Docker)
            - main_file: contents of main entry point (app.py, main.py, etc.)
            - readme: first 2000 chars of README for context
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
        
        # Get file tree (first 150 files)
        try:
            tree_url = f"{cls.BASE_API_URL}/{owner}/{repo}/git/trees/HEAD?recursive=1"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            # Note: fetch_structure doesn't need auth for public repos
            # For private repos, pass token via calling code
            
            response = requests.get(tree_url, headers=headers, timeout=15)
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                # Filter for blobs (files) only
                result['file_list'] = [item['path'] for item in tree[:150] if item['type'] == 'blob']
        except Exception as e:
            logger.warning(f"Failed to fetch file tree: {e}")
        
        def fetch_file(filepath: str, limit: int = 4000) -> str:
            """Helper to fetch a single file from the repo."""
            try:
                # Use raw.githubusercontent.com for file content
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
        result['dockerfile'] = fetch_file('Dockerfile', limit=2000)
        
        # Try to find and fetch main entry point
        entry_points = ['app.py', 'main.py', 'run.py', 'server.py', 'manage.py', 'index.js', 'src/index.js', 'src/main.py']
        for entry in entry_points:
            # Check if file exists in the file list we fetched
            if entry in result['file_list'] or f'src/{entry}' in result['file_list']:
                # If we found it in the list (or just blindly try fetching)
                content = fetch_file(entry, limit=2000)
                if content:
                    result['main_file'] = content
                    break
        
        # Fetch README for additional context
        for readme_name in ['README.md', 'readme.md', 'README.rst', 'README']:
            readme = fetch_file(readme_name, limit=5000) # Increased limit for better AI context
            if readme:
                result['readme'] = readme
                break
        
        return result
