from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

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
        Custom save method to ensure username uniqueness and update profile on login.
        """
        # Handle username collision
        user = sociallogin.user
        base_username = user.username
        counter = 1
        
        # If user PK is None, it's a new user. If exists, we skip collision check (it's them).
        if not user.pk:
            while User.objects.filter(username=user.username).exists():
                user.username = f"{base_username}_{counter}"
                counter += 1
        
        user = super().save_user(request, sociallogin, form)
        
        # Update profile data on every login
        extra_data = sociallogin.account.extra_data
        
        user.github_avatar_url = extra_data.get('avatar_url', '') or user.github_avatar_url
        user.bio = extra_data.get('bio') or user.bio
        user.website = extra_data.get('blog') or user.website
        user.github_public_repos = extra_data.get('public_repos', 0)
        
        # Save specific fields to avoid overwriting unrelated data
        user.save(update_fields=['github_avatar_url', 'bio', 'website', 'github_public_repos'])
        
        return user
