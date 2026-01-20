from django.db import models
from django.conf import settings
from django.utils.text import slugify
from projects.models import Project

class Topic(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Discussion'),
        ('help', 'Help & Support'),
        ('showcase', 'Show & Tell'),
        ('ideas', 'Feedback & Ideas'),
        ('project', 'Project Discussion'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    content = models.TextField()
    
    # Optional link to a specific project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure unique slug
            original_slug = self.slug
            count = 1
            while Topic.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{count}"
                count += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Reply(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_solution = models.BooleanField(default=False)

    def __str__(self):
        return f"Reply by {self.author} on {self.topic}"
