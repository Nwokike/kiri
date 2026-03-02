import os
import re
import requests
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Centralized service for GitHub interactions.
    Handles URL parsing, API fetching, caching, and rate limiting.
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

            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1]
                if repo.endswith('.git'):
                    repo = repo[:-4]
                return (owner, repo)
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
            'User-Agent': 'Kiri-Labs-Bot',
        }
        github_token = getattr(settings, 'GITHUB_TOKEN', '') or os.environ.get('GITHUB_TOKEN', '')
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
                    'language': data.get('language') or 'Unknown',
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
    def fetch_structure(cls, repo_url):
        """Fetches repository structure and key files using parallel requests."""
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
            'readme': '',
        }

        # Fetch file tree
        try:
            tree_url = f"{cls.BASE_API_URL}/{owner}/{repo}/git/trees/HEAD?recursive=1"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Kiri-Labs-Bot',
            }
            github_token = getattr(settings, 'GITHUB_TOKEN', '') or os.environ.get('GITHUB_TOKEN', '')
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            response = requests.get(tree_url, headers=headers, timeout=15)
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                result['file_list'] = [item['path'] for item in tree[:150] if item['type'] == 'blob']
        except Exception as e:
            logger.warning(f"Failed to fetch file tree: {e}")

        def fetch_file(filepath, limit=4000):
            try:
                url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{filepath}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    return resp.text[:limit]
            except Exception:
                pass
            return ''

        # Parallel file fetches
        file_tasks = {
            'package_json': ('package.json', 4000),
            'requirements_txt': ('requirements.txt', 4000),
            'pyproject_toml': ('pyproject.toml', 4000),
            'dockerfile': ('Dockerfile', 2000),
            'readme': ('README.md', 5000),
        }

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(fetch_file, path, limit): key
                for key, (path, limit) in file_tasks.items()
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    result[key] = future.result()
                except Exception:
                    pass

        # Find entry point
        entry_points = [
            'app.py', 'main.py', 'run.py', 'server.py',
            'manage.py', 'index.js', 'src/index.js', 'src/main.py',
        ]
        for entry in entry_points:
            if entry in result['file_list']:
                content = fetch_file(entry, limit=2000)
                if content:
                    result['main_file'] = content
                    break

        return result

    @classmethod
    def fetch_user_repos(cls, access_token, page=1, per_page=50):
        """Fetches the authenticated user's GitHub repositories."""
        cache_key = f"github_user_repos_{hashlib.sha256(access_token.encode()).hexdigest()}_{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Kiri-Labs-Bot',
            }
            response = requests.get(
                'https://api.github.com/user/repos',
                headers=headers,
                params={
                    'sort': 'updated',
                    'direction': 'desc',
                    'per_page': per_page,
                    'page': page,
                    'type': 'owner',
                },
                timeout=15,
            )
            if response.status_code == 200:
                repos = [
                    {
                        'name': r['name'],
                        'full_name': r['full_name'],
                        'description': r.get('description') or '',
                        'html_url': r['html_url'],
                        'language': r.get('language') or '',
                        'stars': r.get('stargazers_count', 0),
                        'forks': r.get('forks_count', 0),
                        'topics': r.get('topics', []),
                        'private': r.get('private', False),
                        'updated_at': r.get('updated_at', ''),
                    }
                    for r in response.json()
                    if not r.get('fork')
                ]
                cache.set(cache_key, repos, 300)  # 5 min cache
                return repos
        except Exception as e:
            logger.error(f"Error fetching user repos: {e}")

        return []


class HuggingFaceService:
    """Service for Hugging Face API interactions."""

    @classmethod
    def fetch_user_repos(cls, access_token, username=None):
        """Fetches the authenticated user's HuggingFace models/datasets."""
        if not username:
            # Get username from token
            try:
                resp = requests.get(
                    'https://huggingface.co/api/whoami-v2',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10,
                )
                if resp.status_code == 200:
                    username = resp.json().get('name', '')
                else:
                    return []
            except Exception as e:
                logger.error(f"HuggingFace whoami failed: {e}")
                return []

        cache_key = f"hf_user_repos_{username}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        repos = []
        try:
            # Fetch models
            resp = requests.get(
                f'https://huggingface.co/api/models?author={username}&sort=lastModified&direction=-1&limit=50',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=15,
            )
            if resp.status_code == 200:
                for m in resp.json():
                    repos.append({
                        'name': m.get('modelId', '').split('/')[-1],
                        'full_name': m.get('modelId', ''),
                        'description': m.get('pipeline_tag') or m.get('library_name') or 'Model',
                        'html_url': f"https://huggingface.co/{m.get('modelId', '')}",
                        'language': m.get('library_name') or '',
                        'stars': m.get('likes', 0),
                        'forks': m.get('downloads', 0),
                        'topics': m.get('tags', [])[:10],
                        'private': m.get('private', False),
                        'updated_at': m.get('lastModified', ''),
                        'type': 'model',
                    })

            # Fetch datasets
            resp = requests.get(
                f'https://huggingface.co/api/datasets?author={username}&sort=lastModified&direction=-1&limit=50',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=15,
            )
            if resp.status_code == 200:
                for d in resp.json():
                    repos.append({
                        'name': d.get('id', '').split('/')[-1],
                        'full_name': d.get('id', ''),
                        'description': 'Dataset',
                        'html_url': f"https://huggingface.co/datasets/{d.get('id', '')}",
                        'language': '',
                        'stars': d.get('likes', 0),
                        'forks': d.get('downloads', 0),
                        'topics': d.get('tags', [])[:10],
                        'private': d.get('private', False),
                        'updated_at': d.get('lastModified', ''),
                        'type': 'dataset',
                    })

            cache.set(cache_key, repos, 300)
        except Exception as e:
            logger.error(f"Error fetching HuggingFace repos: {e}")

        return repos
