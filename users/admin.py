from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserIntegration


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "username", "github_username", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_superuser", "is_active", "role", "is_verified"]
    search_fields = ["email", "username", "github_username"]
    ordering = ["-created_at"]
    
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("bio", "github_username", "github_avatar_url", "website", "research_interests", "is_profile_public")}),
        ("Status", {"fields": ("role", "is_verified", "orcid_id")}),
    )


@admin.register(UserIntegration)
class UserIntegrationAdmin(admin.ModelAdmin):
    list_display = ["user", "platform", "platform_username", "has_repo_scope", "is_primary", "created_at"]
    list_filter = ["platform", "has_repo_scope", "has_write_scope", "is_primary"]
    search_fields = ["user__username", "platform_username"]
    raw_id_fields = ["user"]
    readonly_fields = ["access_token", "refresh_token", "created_at", "updated_at"]
    
    def get_readonly_fields(self, request, obj=None):
        # Don't display actual tokens in admin
        if obj:
            return self.readonly_fields + ["platform"]
        return self.readonly_fields

