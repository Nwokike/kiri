from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Publication(models.Model):
    """
    District 1: The Library. Executable Research Papers.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    abstract = models.TextField(help_text="Brief summary.")
    content = models.TextField(help_text="Main content in Markdown.")
    
    # Metadata
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_publications")
    contributors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='contributed_publications', blank=True)
    version = models.PositiveIntegerField(default=1)
    
    # Academic Identifiers
    arxiv_id = models.CharField(max_length=20, blank=True, help_text="arXiv ID if applicable")
    bibtex = models.TextField(blank=True, help_text="BibTeX citation")

    # Interactive Component (Client-side)
    executable_script = models.TextField(
        blank=True,
        help_text="Python/JS code for in-browser execution (Pyodide)."
    )

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
