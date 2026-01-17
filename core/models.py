from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Comment(models.Model):
    """
    Threaded comments for any content type (Projects, Publications).
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=10000)  # 10KB limit
    
    # Generic Relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Threading
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.author}: {preview}"


class Favorite(models.Model):
    """
    User's favorited items (projects, publications, tools).
    Supports GitHub star syncing when user has repo scope.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # GitHub sync tracking
    github_synced = models.BooleanField(default=False, help_text="Whether this like was synced to GitHub stars")
    sync_failed = models.BooleanField(default=False, help_text="Last sync attempt failed")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} ❤️ {self.content_object}"


class Notification(models.Model):
    """
    User notifications system.
    """
    class Type(models.TextChoices):
        LIKE = 'like', 'Someone liked your content'
        COMMENT = 'comment', 'New comment on your content'
        FOLLOW = 'follow', 'New follower'
        MENTION = 'mention', 'You were mentioned'
        SYSTEM = 'system', 'System notification'
        INTEGRATION = 'integration', 'Integration update'
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    
    # Optional link to related content
    link = models.URLField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Optional actor (who triggered the notification)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='triggered_notifications')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title}"

