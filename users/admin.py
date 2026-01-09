from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "username", "github_username", "is_staff", "created_at"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["email", "username", "github_username"]
    ordering = ["-created_at"]
    
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("bio", "github_username", "website", "avatar", "research_interests")}),
    )
