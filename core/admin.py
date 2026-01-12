from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_type', 'created_at', 'parent']
    list_filter = ['content_type', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['author', 'parent']
    readonly_fields = ['content_type', 'object_id', 'created_at', 'updated_at']
