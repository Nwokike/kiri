from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserIntegration


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "username", "github_username", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["email", "username", "github_username"]
    ordering = ["-created_at"]
    
    fieldsets = UserAdmin.fieldsets + (
        ("GitHub / HuggingFace", {"fields": ("github_username", "github_avatar_url", "huggingface_avatar_url", "github_public_repos")}),
    )


@admin.register(UserIntegration)
class UserIntegrationAdmin(admin.ModelAdmin):
    list_display = ["user", "platform", "platform_username", "has_repo_scope", "is_primary", "created_at"]
    list_filter = ["platform", "has_repo_scope", "has_write_scope", "is_primary"]
    search_fields = ["user__username", "platform_username"]
    raw_id_fields = ["user"]
    readonly_fields = ["masked_access_token", "masked_refresh_token", "created_at", "updated_at"]
    
    def masked_access_token(self, obj):
        return "********" if obj.access_token else "None"
    masked_access_token.short_description = "Access Token"

    def masked_refresh_token(self, obj):
        return "********" if obj.refresh_token else "None"
    masked_refresh_token.short_description = "Refresh Token"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ["platform"]
        return self.readonly_fields
