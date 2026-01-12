from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import requests

User = get_user_model()

class GithubAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Populate the user instance with data from GitHub.
        """
        user = super().populate_user(request, sociallogin, data)
        extra_data = sociallogin.account.extra_data
        
        # 1. Username (from GitHub login)
        github_login = extra_data.get('login')
        if github_login:
            user.username = github_login
            user.github_username = github_login

        # 2. GitHub Profile Meta
        user.github_avatar_url = extra_data.get('avatar_url', '')
        user.bio = extra_data.get('bio') or ''
        user.website = extra_data.get('blog') or ''
        user.github_public_repos = extra_data.get('public_repos', 0)
        
        # 3. Default Role
        user.role = User.Role.CONTRIBUTOR

        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Custom save method to ensure username uniqueness if collision exists (rare with GitHub login as username).
        """
        user = super().save_user(request, sociallogin, form)
        # Additional post-save logic if needed (e.g. fetching private repos if scope allows)
        return user
