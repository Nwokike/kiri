from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model with additional fields for Kiri Research Labs."""
    
    bio = models.TextField(max_length=500, blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    
    # Research interests
    research_interests = models.TextField(blank=True, help_text="Comma-separated research interests")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.email or self.username
