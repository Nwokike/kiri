from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

class Project(models.Model):
    """Project showcase for Kiri Labs."""
    
    class Category(models.TextChoices):
        AI_NLP = 'ai_nlp', 'AI / NLP'
        AI_VISION = 'ai_vision', 'AI / Computer Vision'
        DATA_SCIENCE = 'data_science', 'Data Science'
        WEB_TOOLS = 'web_tools', 'Web Tools'
        AI_AUDIO = 'ai_audio', 'AI / Audio & Speech'
        ML_OPS = 'ml_ops', 'MLOps / Infra'
        ROBOTICS = 'robotics', 'Robotics'
        RESEARCH = 'research', 'Research'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=5000)
    category = models.CharField(
        max_length=50, 
        choices=Category.choices, 
        default=Category.OTHER
    )

    # Links
    github_repo_url = models.URLField(help_text="URL to the GitHub repository")
    demo_url = models.URLField(blank=True, null=True, help_text="Live demo URL (e.g. Vercel/Cloudflare deployment)")
    huggingface_url = models.URLField(blank=True, null=True, help_text="Link to Hugging Face model/dataset")

    # Metrics (Synced from GitHub + Internal)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, blank=True)
    topics = models.JSONField(default=list, blank=True)
    
    # Status
    is_hot = models.BooleanField(default=False, help_text="Automated 'HOT' status based on engagement")
    is_approved = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_approved', 'is_hot']),
            models.Index(fields=['is_approved', '-stars_count']),
            models.Index(fields=['is_approved', '-created_at']),
            models.Index(fields=['submitted_by']),
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("projects:detail", kwargs={"slug": self.slug})
