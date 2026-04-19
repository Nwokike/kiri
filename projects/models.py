import logging
from django.db import models
from django.utils.text import slugify
from django.core.cache import cache
from .services import GitHubService

logger = logging.getLogger(__name__)

class Project(models.Model):
    """Project showcase for Kiri Research Labs."""

    class Category(models.TextChoices):
        AI_NLP = 'ai_nlp', 'AI / NLP'
        AI_VISION = 'ai_vision', 'AI / Computer Vision'
        DATA_SCIENCE = 'data_science', 'Data Science'
        WEB_TOOLS = 'web_tools', 'Web Tools'
        WEB_APPS = 'web_apps', 'Web Applications'
        AI_AUDIO = 'ai_audio', 'AI / Audio & Speech'
        ML_OPS = 'ml_ops', 'MLOps / Infra'
        ROBOTICS = 'robotics', 'Robotics'
        AGENT = 'agent', 'AI Agents'
        RESEARCH = 'research', 'Research'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        BETA = 'beta', 'Beta'
        DEVELOPMENT = 'development', 'In Development'
        ARCHIVED = 'archived', 'Archived'

    # ── Core Info ──
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=5000)
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    # ── Links ──
    github_repo_url = models.URLField(
        blank=True, default='',
        help_text="GitHub repository URL",
    )
    huggingface_url = models.URLField(
        blank=True, default='',
        help_text="Hugging Face Space/Model/Dataset URL",
    )
    live_url = models.URLField(
        blank=True, default='',
        help_text="Production URL (e.g. https://imara.kiri.ng)",
    )
    staging_url = models.URLField(
        blank=True, default='',
        help_text="Beta/staging URL for non-live projects",
    )
    custom_image_url = models.URLField(
        blank=True, default='',
        help_text="Override image URL (leave blank to use GitHub OG image)",
    )

    # ── Metadata (synced from GitHub, kept for internal reference) ──
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    language = models.CharField(max_length=50, blank=True, default='')
    topics = models.CharField(
        max_length=500, blank=True, default='',
        help_text="Comma-separated tags (auto-synced from GitHub if empty)",
    )
    tech_stack = models.CharField(
        max_length=500, blank=True, default='',
        help_text="Curated tech stack badges, comma-separated (e.g. Django, TinyML, Groq)",
    )

    # ── Display ──
    is_featured = models.BooleanField(
        default=False,
        help_text="Manually feature this project on the homepage",
    )

    # ── SEO ──
    seo_title = models.CharField(
        max_length=70, blank=True, default='',
        help_text="Custom SEO title (overrides project name in <title>)",
    )
    seo_description = models.CharField(
        max_length=160, blank=True, default='',
        help_text="Custom meta description for search engines",
    )

    # ── Timestamps ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]

    # ── Properties ──

    @property
    def preview_image_url(self):
        """Return image URL: custom override → GitHub OG image → Hugging Face OG image → None."""
        if self.custom_image_url:
            return self.custom_image_url
            
        if self.github_repo_url:
            parsed = GitHubService.parse_repo_url(self.github_repo_url)
            if parsed:
                owner, repo = parsed
                return f"https://opengraph.githubassets.com/1/{owner}/{repo}"
                
        if self.huggingface_url:
            url = self.huggingface_url.split('#')[0].split('?')[0].rstrip('/')
            if 'huggingface.co/' in url:
                path = url.split('huggingface.co/')[-1]
                parts = [p for p in path.split('/') if p]
                if len(parts) >= 2:
                    if parts[0] in ('spaces', 'datasets', 'models'):
                        hf_type = parts[0]
                        owner = parts[1]
                        repo = parts[2] if len(parts) > 2 else ""
                        if repo:
                            return f"https://cdn-thumbnails.huggingface.co/social-thumbnails/{hf_type}/{owner}/{repo}.png"
                        else:
                            return f"https://cdn-thumbnails.huggingface.co/social-thumbnails/{hf_type}/{owner}.png"
                    else:
                        owner = parts[0]
                        repo = parts[1]
                        return f"https://cdn-thumbnails.huggingface.co/social-thumbnails/models/{owner}/{repo}.png"
                        
        return None

    @property
    def is_kiri_platform(self):
        """Check if this project is hosted on a *.kiri.ng subdomain."""
        return bool(self.live_url and 'kiri.ng' in self.live_url)

    @property
    def primary_url(self):
        """Return the best URL to showcase: live > staging > repo."""
        return self.live_url or self.staging_url or self.github_repo_url

    @property
    def tech_stack_list(self):
        """Return tech stack as a list for template iteration."""
        if not self.tech_stack:
            return []
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    @property
    def topics_list(self):
        """Return topics as a list for template iteration."""
        if not self.topics:
            return []
        return [t.strip() for t in self.topics.split(',') if t.strip()]

    # ── Save / Display ──

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        cache.delete('homepage_context')
        
        # Auto-post to Facebook if new and credentials exist
        if is_new:
            from kiri_project.tasks import post_to_facebook
            from django.db import transaction
            try:
                transaction.on_commit(lambda: post_to_facebook('project', self.id))
            except Exception as e:
                # We don't want to fail the save if FB posting fails
                logger.error(f"Failed to queue initial FB post for project {self.name}: {e}")


    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('homepage_context')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("projects:detail", kwargs={"slug": self.slug})
