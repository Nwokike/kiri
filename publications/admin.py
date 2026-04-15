from django.contrib import admin
from .models import Publication

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'repo_name', 'published_at', 'last_synced_at')
    search_fields = ('title', 'repo_name', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('last_synced_at', 'created_at', 'updated_at')
