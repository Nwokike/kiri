from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Project(models.Model):
    """
    The Colosseum: Showcase of projects.
    """
    class Category(models.TextChoices):
        AI_NLP = 'ai_nlp', 'AI / NLP'
        AI_VISION = 'ai_vision', 'AI / Computer Vision'
        DATA_SCIENCE = 'data_science', 'Data Science'
        WEB_TOOLS = 'web_tools', 'Web Tools'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(
        max_length=50, 
        choices=Category.choices, 
        default=Category.OTHER
    )

    # Links
    github_repo_url = models.URLField(help_text="URL to the GitHub repository")
    demo_url = models.URLField(blank=True, null=True, help_text="Live demo URL")
    huggingface_url = models.URLField(blank=True, default='', help_text="Link to Hugging Face model/dataset")

    # Metrics (Synced from GitHub + Internal)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, blank=True)
    topics = models.JSONField(default=list, blank=True)
    
    # Kiri State
    is_hot = models.BooleanField(default=False, help_text="Automated 'HOT' status based on engagement")
    is_approved = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
