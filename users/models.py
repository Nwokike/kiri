from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, URLValidator
from django.urls import reverse
from django.utils import timezone

orcid_validator = RegexValidator(
    regex=r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$',
    message='Enter a valid ORCID iD (e.g., 0000-0001-2345-6789)'
)

class CustomUser(AbstractUser):
    """
    Extended user model for Kiri Research Labs.
    Username is auto-generated from GitHub login.
    """
    
    class Role(models.TextChoices):
        VISITOR = 'visitor', _('Visitor')
        CONTRIBUTOR = 'contributor', _('Contributor')
        RESEARCHER = 'researcher', _('Researcher')
        CORE_TEAM = 'core_team', _('Core Team')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRIBUTOR,
        help_text="User's role in the platform."
    )
    
    bio = models.TextField(max_length=500, blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    github_avatar_url = models.URLField(blank=True, help_text="Avatar URL synced from GitHub")
    github_public_repos = models.IntegerField(default=0, help_text="Number of public repos")
    
    website = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
        help_text="Personal or research website (http/https only)"
    )
    orcid_id = models.CharField(
        max_length=20, 
        blank=True, 
        validators=[orcid_validator],
        help_text="Researcher ORCID iD (format: 0000-0000-0000-000X)"
    )
    
    is_verified = models.BooleanField(default=False, help_text="Verified researcher status")
    is_profile_public = models.BooleanField(default=True, help_text="Allow others to view your profile")
    research_interests = models.JSONField(default=list, blank=True, help_text="List of research topics")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['github_username']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.username
        
    def get_absolute_url(self):
        return reverse("users:profile", kwargs={"username": self.username})
    
    def get_primary_integration(self):
        """Get the user's primary integration for content creation."""
        return self.integrations.filter(is_primary=True).first()


class UserIntegration(models.Model):
    """
    Stores user's connected platform integrations.
    Each integration stores OAuth tokens for API access.
    """
    class Platform(models.TextChoices):
        GITHUB = 'github', 'GitHub'
        GITLAB = 'gitlab', 'GitLab'
        BITBUCKET = 'bitbucket', 'Bitbucket'
        HUGGINGFACE = 'huggingface', 'Hugging Face'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integrations')
    platform = models.CharField(max_length=20, choices=Platform.choices)
    platform_username = models.CharField(max_length=100, help_text="Username on the platform")
    platform_user_id = models.CharField(max_length=100, blank=True, help_text="User ID on the platform")
    avatar_url = models.URLField(blank=True)
    
    # OAuth tokens (encrypted in production via application-level encryption)
    access_token = models.TextField(help_text="OAuth access token")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token if available")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def is_token_expired(self):
        """Check if the access token has expired."""
        if not self.token_expires_at:
            return False  # No expiry set, assume not expired
        return timezone.now() >= self.token_expires_at
    
    # Scope tracking for incremental authorization
    granted_scopes = models.JSONField(default=list, blank=True, help_text="List of granted OAuth scopes")
    has_repo_scope = models.BooleanField(default=False, help_text="Can star repositories")
    has_write_scope = models.BooleanField(default=False, help_text="Can create repositories")
    
    # Primary integration for content creation
    is_primary = models.BooleanField(default=False)
    
    # Flag to track if tokens are encrypted (for migration)
    tokens_encrypted = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'platform']
        indexes = [
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['platform']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_platform_display()}"
    
    def get_decrypted_access_token(self):
        """Get decrypted access token for API calls."""
        if not self.access_token:
            return ""
        if not self.tokens_encrypted:
            return self.access_token
        from .encryption import decrypt_token
        return decrypt_token(self.access_token)
    
    def set_encrypted_access_token(self, token):
        """Set and encrypt access token."""
        if not token:
            self.access_token = ""
            return
        from .encryption import encrypt_token
        self.access_token = encrypt_token(token)
        self.tokens_encrypted = True
    
    def get_decrypted_refresh_token(self):
        """Get decrypted refresh token."""
        if not self.refresh_token:
            return ""
        if not self.tokens_encrypted:
            return self.refresh_token
        from .encryption import decrypt_token
        return decrypt_token(self.refresh_token)
    
    def set_encrypted_refresh_token(self, token):
        """Set and encrypt refresh token."""
        if not token:
            self.refresh_token = ""
            return
        from .encryption import encrypt_token
        self.refresh_token = encrypt_token(token)
        self.tokens_encrypted = True
    
    def save(self, *args, **kwargs):
        # Ensure only one primary integration per user
        if self.is_primary:
            UserIntegration.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        # If this is the first integration, make it primary
        if not self.pk and not UserIntegration.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)

