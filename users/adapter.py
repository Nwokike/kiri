import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from .models import UserIntegration

User = get_user_model()
logger = logging.getLogger(__name__)

class KiriAccountAdapter(DefaultAccountAdapter):
    """Block all public signup - admin/invite-only."""
    def is_open_for_signup(self, request):
        return False

class KiriSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Universal social account adapter for all OAuth providers.
    Handles user creation and auto-creates UserIntegration records.
    """
    def is_open_for_signup(self, request, sociallogin):
        return False
    def pre_social_login(self, request, sociallogin):
        """
        Invoked before a social login is performed.
        Ensures UserIntegration is synced even for existing users.
        """
        if sociallogin.is_existing:
            # Sync user profile fields (avatar, etc)
            self._update_user_from_social(sociallogin.user, sociallogin)
            # Sync integration record
            self._create_or_update_integration(sociallogin.user, sociallogin)
        super().pre_social_login(request, sociallogin)

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
        elif provider == 'huggingface':
            # Hugging Face specific fields
            user.username = extra_data.get('preferred_username', data.get('username', ''))
            user.bio = ''  # HuggingFace doesn't provide bio in OIDC
            user.huggingface_avatar_url = extra_data.get('picture', '')
        
        # Default Role for all users
        user.role = User.Role.CONTRIBUTOR
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and create/update UserIntegration record.
        """
        # Handle username collision for new users
        user = sociallogin.user
        base_username = user.username or 'user'
        counter = 1
        
        if not user.pk:
            while User.objects.filter(username=user.username).exists():
                user.username = f"{base_username}_{counter}"
                counter += 1
        
        user = super().save_user(request, sociallogin, form)
        
        # Update user fields on every login (for all providers)
        self._update_user_from_social(user, sociallogin)
        
        # Create or update UserIntegration
        self._create_or_update_integration(user, sociallogin)
        
        return user

    def save_social_account(self, request, sociallogin):
        """
        Invoked when a social account is being saved (e.g. during linking).
        """
        super().save_social_account(request, sociallogin)
        # Ensure profile fields are synced when a new account is linked
        self._update_user_from_social(sociallogin.user, sociallogin)
        self._create_or_update_integration(sociallogin.user, sociallogin)
    
    def _create_or_update_integration(self, user, sociallogin):
        """Create or update UserIntegration record from OAuth data."""
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        
        # Map provider to platform enum
        platform_map = {
            'github': UserIntegration.Platform.GITHUB,
            'huggingface': UserIntegration.Platform.HUGGINGFACE,
        }
        
        platform = platform_map.get(provider)
        if not platform:
            logger.warning(f"Unknown OAuth provider: {provider}")
            return None
        
        # Get token data
        token = sociallogin.token
        access_token = token.token if token else ''
        # OAuth2 refresh tokens are stored in token.token_secret in allauth
        refresh_token = getattr(token, 'token_secret', '') if token else ''
        if not refresh_token and token:
             # Fallback check for different allauth versions/providers
             refresh_token = getattr(token, 'refresh_token', '')
        
        # Determine scopes granted
        granted_scopes = []
        has_repo_scope = False
        has_write_scope = False
        
        from django.conf import settings
        provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get(provider, {})
        configured_scopes = provider_settings.get('SCOPE', [])
        granted_scopes = configured_scopes
        
        if provider == 'github':
            has_repo_scope = 'public_repo' in configured_scopes or 'repo' in configured_scopes
            has_write_scope = 'repo' in configured_scopes
        elif provider == 'huggingface':
            has_repo_scope = 'read-repos' in configured_scopes
            has_write_scope = 'write-repos' in configured_scopes
        
        # Get platform-specific username, ID, and avatar
        if provider == 'github':
            platform_username = extra_data.get('login', '')
            platform_user_id = str(extra_data.get('id', ''))
            avatar_url = extra_data.get('avatar_url', '')
        elif provider == 'huggingface':
            platform_username = extra_data.get('preferred_username', '')
            platform_user_id = str(extra_data.get('sub', ''))
            avatar_url = extra_data.get('picture', '')
        else:
            platform_username = ''
            platform_user_id = ''
            avatar_url = ''
        
        try:
            # Create or update integration
            integration, created = UserIntegration.objects.update_or_create(
                user=user,
                platform=platform,
                defaults={
                    'platform_username': platform_username,
                    'platform_user_id': platform_user_id,
                    'avatar_url': avatar_url,
                    'granted_scopes': granted_scopes,
                    'has_repo_scope': has_repo_scope,
                    'has_write_scope': has_write_scope,
                }
            )
            # Encrypt and save tokens separately
            integration.set_encrypted_access_token(access_token)
            integration.set_encrypted_refresh_token(refresh_token)
            integration.save(update_fields=['access_token', 'refresh_token', 'tokens_encrypted'])
            
            logger.info(f"{'Created' if created else 'Updated'} {provider} integration for {user.username}")
            return integration
        except Exception as e:
            logger.error(f"Failed to create/update integration for {provider}: {e}")
            return None

    def _update_user_from_social(self, user, sociallogin):
        """
        Update CustomUser fields (avatar, bio, etc) from provider data.
        """
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        update_fields = []

        try:
            if provider == 'github':
                github_avatar = extra_data.get('avatar_url', '')
                if github_avatar and user.github_avatar_url != github_avatar:
                    user.github_avatar_url = github_avatar
                    update_fields.append('github_avatar_url')
                
                github_login = extra_data.get('login', '')
                if github_login and user.github_username != github_login:
                    user.github_username = github_login
                    update_fields.append('github_username')
                
                bio = extra_data.get('bio') or ''
                if bio and user.bio != bio:
                    user.bio = bio
                    update_fields.append('bio')
                
                website = extra_data.get('blog') or ''
                if website and user.website != website:
                    user.website = website
                    update_fields.append('website')
                
                repos = extra_data.get('public_repos', 0)
                if repos != user.github_public_repos:
                    user.github_public_repos = repos
                    update_fields.append('github_public_repos')
                    
            elif provider == 'huggingface':
                hf_avatar = extra_data.get('picture', '')
                if hf_avatar and user.huggingface_avatar_url != hf_avatar:
                    user.huggingface_avatar_url = hf_avatar
                    update_fields.append('huggingface_avatar_url')
            
            if update_fields:
                user.save(update_fields=update_fields)
                logger.info(f"Updated profile fields {update_fields} for {user.username} from {provider}")
                
        except Exception as e:
            logger.warning(f"Failed to sync profile fields for {user.username} from {provider}: {e}")
