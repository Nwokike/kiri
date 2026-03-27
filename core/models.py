from django.db import models


class EcosystemPlatform(models.Model):
    """External platforms in the Kiri ecosystem (shown in navigation)."""
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon_class = models.CharField(
        max_length=50, blank=True, default='fas fa-globe',
        help_text="FontAwesome class for icon",
    )
    short_description = models.CharField(max_length=200, blank=True, default='')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name
