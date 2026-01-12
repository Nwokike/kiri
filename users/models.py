from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.urls import reverse

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
    
    website = models.URLField(blank=True)
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
