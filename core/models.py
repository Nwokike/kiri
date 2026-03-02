from django.db import models
from django.conf import settings

class ErrorLog(models.Model):
    """
    Local error logging for admin.
    Captures 500 errors and other application exceptions.
    """
    ERROR_LEVELS = [
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    
    level = models.CharField(max_length=10, choices=ERROR_LEVELS, default='error')
    path = models.CharField(max_length=500, help_text="Request path where error occurred")
    method = models.CharField(max_length=10, default='GET')
    exception_type = models.CharField(max_length=200, blank=True)
    message = models.TextField(help_text="Error message")
    traceback = models.TextField(blank=True, help_text="Full traceback")
    
    # Optional context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='error_logs'
    )
    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['level', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.path} - {self.message[:50]}"


class EcosystemPlatform(models.Model):
    """
    External revenue platforms integrated into Kiri's navigation.
    Managed via Django admin - no template changes needed.
    """
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon_class = models.CharField(
        max_length=100,
        help_text="FontAwesome or custom icon class, e.g. 'fas fa-store'"
    )
    short_description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Ecosystem Platform'
        verbose_name_plural = 'Ecosystem Platforms'

    def __str__(self):
        return self.name
