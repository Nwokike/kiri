from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Project(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    
    # Metadata
    github_repo_url = models.URLField(help_text="URL to the GitHub repository")
    demo_url = models.URLField(blank=True, null=True, help_text="Live demo URL if available")
    
    # Synced Data (from GitHub)
    stars_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            
        # Hook: Sync on first creation
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.github_repo_url:
            # Import here to avoid circular dependency
            from .utils import sync_project_metadata
            try:
                sync_project_metadata(self)
            except Exception:
                pass # Fail silently on sync for now
