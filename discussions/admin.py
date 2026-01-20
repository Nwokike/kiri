from django.contrib import admin
from .models import Topic, Reply

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_pinned', 'view_count', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_closed', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'is_solution', 'created_at')
    list_filter = ('is_solution', 'created_at')
    search_fields = ('content', 'author__username', 'topic__title')
