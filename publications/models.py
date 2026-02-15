from django.db import models, transaction
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
import re

def validate_path_traversal(value):
    if '..' in value or value.startswith('/') or '//' in value:
        raise ValidationError("Invalid path: path traversal or absolute paths are not allowed.")

class Publication(models.Model):
    """
    District 1: The Library. Executable Research Papers.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    abstract = models.TextField(help_text="Brief summary.")
    content = models.TextField(help_text="Main content in Markdown.")
    
    # GitHub-First Storage
    github_repo_url = models.URLField(max_length=255, blank=True, help_text="URL to the GitHub repository storing content.")
    github_file_path = models.CharField(
        max_length=255, 
        blank=True, 
        validators=[validate_path_traversal],
        help_text="Path to the markdown file within the repo (e.g. docs/paper.md)."
    )
    
    # Metadata
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_publications")
    contributors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='contributed_publications', blank=True)
    view_count = models.PositiveIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    
    # Identifiers
    arxiv_id = models.CharField(max_length=20, blank=True)
    doi = models.CharField(max_length=100, blank=True, help_text="Digital Object Identifier")
    # bibtex field removed as it is auto-generated

    # Interactive Component (Client-side)
    executable_script = models.TextField(
        blank=True,
        help_text="Python/JS code for in-browser execution (Pyodide)."
    )

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        # Slug Generation
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Publication.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        # Version Handling & Revision Creation
        is_new = self.pk is None
        if not is_new:
            with transaction.atomic():
                try:
                    # Use select_for_update to handle concurrent edits
                    old = Publication.objects.select_for_update().get(pk=self.pk)
                    if old.content != self.content:
                        self.version = old.version + 1
                        # Save Revision
                        PublicationRevision.objects.create(
                            publication=self,
                            version=old.version,
                            title=old.title,
                            content=old.content,
                            created_at=old.updated_at
                        )
                except Publication.DoesNotExist:
                    pass
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("publications:detail", kwargs={"slug": self.slug})


class PublicationRevision(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='revisions')
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-version']
        constraints = [
            models.UniqueConstraint(fields=['publication', 'version'], name='unique_publication_version')
        ]
        
    def __str__(self):
        return f"{self.publication.title} v{self.version}"

