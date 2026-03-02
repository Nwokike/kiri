from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Minimal user model for Kiri Labs.
    Serves as admin/team authentication only.
    """
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        CONTRIBUTOR = 'contributor', 'Contributor'
        MEMBER = 'member', 'Member'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.MEMBER
    )
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    
    github_username = models.CharField(max_length=100, blank=True)
    github_avatar_url = models.URLField(blank=True, help_text="Avatar URL synced from GitHub")
    huggingface_avatar_url = models.URLField(blank=True, help_text="Avatar URL synced from Hugging Face")
    github_public_repos = models.IntegerField(default=0, help_text="Number of public repos")
    
    @property
    def avatar_url(self):
        """Get the prioritized avatar URL: GitHub > Hugging Face > Default."""
        if self.github_avatar_url:
            return self.github_avatar_url
        if self.huggingface_avatar_url:
            return self.huggingface_avatar_url
        return None

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['github_username']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.username


class UserIntegration(models.Model):
    """
    Stores user's connected platform integrations.
    Each integration stores OAuth tokens for API access.
    """
    class Platform(models.TextChoices):
        GITHUB = 'github', 'GitHub'
        HUGGINGFACE = 'huggingface', 'Hugging Face'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integrations')
    platform = models.CharField(max_length=20, choices=Platform.choices)
    platform_username = models.CharField(max_length=100, help_text="Username on the platform")
    platform_user_id = models.CharField(max_length=100, blank=True, help_text="User ID on the platform")
    avatar_url = models.URLField(blank=True)
    
    # OAuth tokens (encrypted in production)
    access_token = models.TextField(help_text="OAuth access token")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token if available")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def is_token_expired(self):
        if not self.token_expires_at:
            return False
        return timezone.now() >= self.token_expires_at
    
    # Scope tracking
    granted_scopes = models.JSONField(default=list, blank=True, help_text="List of granted OAuth scopes")
    has_repo_scope = models.BooleanField(default=False, help_text="Can star repositories")
    has_write_scope = models.BooleanField(default=False, help_text="Can create repositories")
    
    is_primary = models.BooleanField(default=False)
    tokens_encrypted = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'platform'], name='unique_user_platform')
        ]
        indexes = [
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['platform']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_platform_display()}"
    
    def get_decrypted_access_token(self):
        if not self.access_token:
            return ""
        if not self.tokens_encrypted:
            return self.access_token
        from .encryption import decrypt_token
        return decrypt_token(self.access_token)
    
    def set_encrypted_access_token(self, token):
        if not token:
            self.access_token = ""
            return
        from .encryption import encrypt_token
        self.access_token = encrypt_token(token)
        self.tokens_encrypted = True
    
    def get_decrypted_refresh_token(self):
        if not self.refresh_token:
            return ""
        if not self.tokens_encrypted:
            return self.refresh_token
        from .encryption import decrypt_token
        return decrypt_token(self.refresh_token)
    
    def set_encrypted_refresh_token(self, token):
        if not token:
            self.refresh_token = ""
            return
        from .encryption import encrypt_token
        self.refresh_token = encrypt_token(token)
        self.tokens_encrypted = True
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            UserIntegration.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        if not self.pk and not UserIntegration.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)
