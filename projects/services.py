import os
import re
import requests
import logging
from urllib.parse import urlparse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Centralized service for GitHub interactions.
    Handles URL parsing, API fetching, and caching.
    """

    BASE_API_URL = "https://api.github.com/repos"

    @staticmethod
    def parse_repo_url(url):
        """Parses a GitHub URL and returns (owner, repo_name) or None."""
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

            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) >= 2:
                repo_name = path_parts[1].removesuffix('.git')
                return path_parts[0], repo_name
        except Exception:
            return None

        return None

    @classmethod
    def fetch_repo_data(cls, repo_url):
        """Fetches metadata for a repo with caching."""
        parsed = cls.parse_repo_url(repo_url)
        if not parsed:
            return None

        owner, repo = parsed
        cache_key = f"github_meta:{owner}:{repo}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        api_url = f"{cls.BASE_API_URL}/{owner}/{repo}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Kiri-Research-Labs',
        }
        github_token = os.environ.get('GITHUB_TOKEN', '')
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        try:
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code in [403, 429]:
                logger.warning("GitHub Rate Limit Hit.")
                return None

            if response.status_code == 200:
                data = response.json()
                result = {
                    'stars_count': data.get('stargazers_count', 0),
                    'forks_count': data.get('forks_count', 0),
                    'language': data.get('language') or '',
                    'description': data.get('description', ''),
                    'topics': data.get('topics', []),
                    'last_updated': timezone.now().isoformat(),
                }
                cache.set(cache_key, result, 3600)
                return result

        except Exception as e:
            logger.error(f"GitHub API Error for {repo_url}: {e}")
            return None

        return None

    @classmethod
    def fetch_user_public_repos(cls, username):
        """Fetches all public repos for a GitHub user. Used by sync management command."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Kiri-Research-Labs',
        }
        github_token = os.environ.get('GITHUB_TOKEN', '')
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        repos = []
        page = 1

        while True:
            try:
                response = requests.get(
                    f"https://api.github.com/users/{username}/repos",
                    params={'type': 'public', 'per_page': 100, 'page': page},
                    headers=headers,
                    timeout=15,
                )
                if response.status_code != 200:
                    break

                batch = response.json()
                if not batch:
                    break

                repos.extend(batch)
                page += 1

                if len(batch) < 100:
                    break
            except Exception as e:
                logger.error(f"Error fetching repos for {username}: {e}")
                break

        return repos
