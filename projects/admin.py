from django.contrib import admin
from .models import Project, ProjectInsight

@admin.register(ProjectInsight)
class ProjectInsightAdmin(admin.ModelAdmin):
    list_display = ('project', 'complexity_score', 'ai_model_used', 'last_analyzed_at')
    search_fields = ('project__name', 'summary')
    readonly_fields = ('last_analyzed_at',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitted_by', 'stars_count', 'language', 'is_approved', 'is_hot', 'created_at')
    list_filter = ('is_approved', 'is_hot', 'language', 'category', 'created_at')
    search_fields = ('name', 'description', 'submitted_by__username')
    prepopulated_fields = {'slug': ('name',)}
    actions = ['approve_projects', 'reject_projects', 'mark_hot', 'sync_github', 'analyze_with_ai']
    
    @admin.action(description='Approve selected projects')
    def approve_projects(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description='Reject/Unapprove selected projects')
    def reject_projects(self, request, queryset):
        queryset.update(is_approved=False)
    
    @admin.action(description='Mark as HOT')
    def mark_hot(self, request, queryset):
        queryset.update(is_hot=True)

    @admin.action(description='Sync from GitHub')
    def sync_github(self, request, queryset):
        from .utils import sync_project_metadata
        count = 0
        for project in queryset:
            if sync_project_metadata(project):
                count += 1
        self.message_user(request, f"Synced {count} projects.")

    @admin.action(description='Analyze with AI (Advisor)')
    def analyze_with_ai(self, request, queryset):
        from kiri_project.tasks import analyze_project_task
        for project in queryset:
            analyze_project_task(project.id)
        self.message_user(request, f"Queued AI analysis for {queryset.count()} projects.")
