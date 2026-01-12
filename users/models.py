from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

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
    orcid_id = models.CharField(max_length=20, blank=True, help_text="Researcher ORCID iD")
    
    is_verified = models.BooleanField(default=False, help_text="Verified researcher status")
    research_interests = models.TextField(blank=True, help_text="Comma-separated interests")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
