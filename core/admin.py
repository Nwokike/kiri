from django.contrib import admin
from .models import ErrorLog, EcosystemPlatform


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'path', 'exception_type', 'is_resolved', 'created_at']
    list_filter = ['level', 'is_resolved', 'created_at']
    search_fields = ['path', 'message', 'exception_type']
    readonly_fields = ['level', 'path', 'method', 'exception_type', 'message', 'traceback', 'user', 'user_agent', 'ip_address', 'created_at']
    list_per_page = 50
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
    mark_as_resolved.short_description = "Mark selected errors as resolved"


@admin.register(EcosystemPlatform)
class EcosystemPlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'display_order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'url']
