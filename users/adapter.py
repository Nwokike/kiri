from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from .models import UserIntegration

User = get_user_model()


class KiriSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Universal social account adapter for all OAuth providers.
    Handles user creation and auto-creates UserIntegration records.
    """
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate the user instance with data from any social provider.
        """
        user = super().populate_user(request, sociallogin, data)
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        
        if provider == 'github':
            # GitHub specific fields
            github_login = extra_data.get('login')
            if github_login:
                user.username = github_login
                user.github_username = github_login
            user.github_avatar_url = extra_data.get('avatar_url', '')
            user.bio = extra_data.get('bio') or ''
            user.website = extra_data.get('blog') or ''
            user.github_public_repos = extra_data.get('public_repos', 0)
            
        elif provider == 'gitlab':
            # GitLab specific fields
            user.username = extra_data.get('username', data.get('username', ''))
            user.bio = extra_data.get('bio') or ''
            user.website = extra_data.get('web_url') or ''
            
        elif provider == 'bitbucket_oauth2':
            # Bitbucket specific fields
            user.username = extra_data.get('username', data.get('username', ''))
            user.website = extra_data.get('links', {}).get('html', {}).get('href', '')
        
        # Default Role for all users
        user.role = User.Role.CONTRIBUTOR
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and create/update UserIntegration record.
        """
        # Handle username collision for new users
        user = sociallogin.user
        base_username = user.username
        counter = 1
        
        if not user.pk:
            while User.objects.filter(username=user.username).exists():
                user.username = f"{base_username}_{counter}"
                counter += 1
        
        user = super().save_user(request, sociallogin, form)
        
        # Update user fields on every login (for GitHub)
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        
        if provider == 'github':
            user.github_avatar_url = extra_data.get('avatar_url', '') or user.github_avatar_url
            user.bio = extra_data.get('bio') or user.bio
            user.website = extra_data.get('blog') or user.website
            user.github_public_repos = extra_data.get('public_repos', 0)
            user.save(update_fields=['github_avatar_url', 'bio', 'website', 'github_public_repos'])
        
        # Create or update UserIntegration
        self._create_or_update_integration(user, sociallogin)
        
        return user
    
    def _create_or_update_integration(self, user, sociallogin):
        """Create or update UserIntegration record from OAuth data."""
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        
        # Map provider to platform enum
        platform_map = {
            'github': UserIntegration.Platform.GITHUB,
            'gitlab': UserIntegration.Platform.GITLAB,
            'bitbucket_oauth2': UserIntegration.Platform.BITBUCKET,
            'huggingface': UserIntegration.Platform.HUGGINGFACE,
        }
        
        platform = platform_map.get(provider)
        if not platform:
            return  # Unknown provider
        
        # Get token data
        token = sociallogin.token
        access_token = token.token if token else ''
        refresh_token = getattr(token, 'token_secret', '') if token else ''
        
        # Determine scopes granted
        granted_scopes = []
        has_repo_scope = False
        has_write_scope = False
        
        if provider == 'github':
            # GitHub scope is set in settings
            from django.conf import settings
            configured_scopes = settings.SOCIALACCOUNT_PROVIDERS.get('github', {}).get('SCOPE', [])
            granted_scopes = configured_scopes
            has_repo_scope = 'public_repo' in configured_scopes or 'repo' in configured_scopes
            has_write_scope = 'repo' in configured_scopes
        
        # Get platform-specific username
        if provider == 'github':
            platform_username = extra_data.get('login', '')
            platform_user_id = str(extra_data.get('id', ''))
            avatar_url = extra_data.get('avatar_url', '')
        elif provider == 'gitlab':
            platform_username = extra_data.get('username', '')
            platform_user_id = str(extra_data.get('id', ''))
            avatar_url = extra_data.get('avatar_url', '')
        elif provider == 'bitbucket_oauth2':
            platform_username = extra_data.get('username', '')
            platform_user_id = extra_data.get('uuid', '')
            avatar_url = extra_data.get('links', {}).get('avatar', {}).get('href', '')
        else:
            platform_username = ''
            platform_user_id = ''
            avatar_url = ''
        
        # Create or update integration
        integration, created = UserIntegration.objects.update_or_create(
            user=user,
            platform=platform,
            defaults={
                'platform_username': platform_username,
                'platform_user_id': platform_user_id,
                'avatar_url': avatar_url,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'granted_scopes': granted_scopes,
                'has_repo_scope': has_repo_scope,
                'has_write_scope': has_write_scope,
            }
        )
        
        return integration

