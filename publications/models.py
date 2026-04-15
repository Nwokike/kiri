from django.db import models
from django.utils import timezone
from django.urls import reverse

class Publication(models.Model):
    repo_name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    html_content = models.TextField()
    github_url = models.URLField()
    topics = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('publications:detail', kwargs={'slug': self.slug})

    @property
    def topics_list(self):
        if not self.topics:
            return []
        return [t.strip() for t in self.topics.split(',')]
