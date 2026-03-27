from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'is_featured', 'live_url', 'created_at')
    list_filter = ('status', 'is_featured', 'category', 'language', 'created_at')
    search_fields = ('name', 'description', 'github_repo_url', 'tech_stack')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status', 'is_featured']
    actions = ['mark_featured', 'unmark_featured', 'sync_github']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'category', 'status'),
        }),
        ('Links', {
            'fields': ('github_repo_url', 'live_url', 'staging_url', 'custom_image_url'),
        }),
        ('Display', {
            'fields': ('is_featured', 'tech_stack', 'language', 'topics'),
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',),
        }),
        ('GitHub Sync (read-only)', {
            'fields': ('stars_count', 'forks_count', 'last_synced_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('stars_count', 'forks_count', 'last_synced_at')

    @admin.action(description='Mark as Featured')
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove from Featured')
    def unmark_featured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description='Sync from GitHub')
    def sync_github(self, request, queryset):
        from .utils import sync_project_metadata
        count = 0
        for project in queryset:
            if sync_project_metadata(project):
                count += 1
        self.message_user(request, f"Synced {count} projects.")
