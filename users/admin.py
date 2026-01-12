from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


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
