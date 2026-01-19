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
        
        # Add Token if available from environment
        import os
        token = os.environ.get('GITHUB_TOKEN')
        
        if token:
            headers['Authorization'] = f'token {token}'
            
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
