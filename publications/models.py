from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Publication(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    abstract = models.TextField(help_text="A brief summary of the research paper.")
    content = models.TextField(help_text="The main content in Markdown format.")
    
    # The 'Living' part: Client-side executable code
    executable_script = models.TextField(
        blank=True, 
        help_text="JavaScript code that runs client-side for the interactive demo."
    )
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
