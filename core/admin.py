from django.contrib import admin
from .models import EcosystemPlatform


@admin.register(EcosystemPlatform)
class EcosystemPlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'display_order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'url']
