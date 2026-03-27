from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Minimal user model for Kiri Research Labs.
    Only used for staff/admin authentication.
    """
    github_username = models.CharField(max_length=100, blank=True, default='')
    github_avatar_url = models.URLField(blank=True, default='', help_text="Avatar URL from GitHub")

    @property
    def avatar_url(self):
        """Get avatar: GitHub > Gravatar-style default."""
        return self.github_avatar_url or None

    class Meta:
        indexes = [
            models.Index(fields=['github_username']),
        ]

    def __str__(self):
        return self.username
