from django.contrib import admin
from .models import Comment, Favorite, Notification, ErrorLog


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_type', 'created_at', 'parent']
    list_filter = ['content_type', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['author', 'parent']
    readonly_fields = ['content_type', 'object_id', 'created_at', 'updated_at']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'created_at', 'github_synced']
    list_filter = ['content_type', 'github_synced', 'sync_failed']
    search_fields = ['user__username']
    raw_id_fields = ['user']
    readonly_fields = ['content_type', 'object_id', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['title', 'recipient__username']
    raw_id_fields = ['recipient', 'actor']
    readonly_fields = ['created_at']


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
