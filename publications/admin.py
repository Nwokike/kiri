from django.contrib import admin
from .models import Publication, PublicationRevision


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'version', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'abstract')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['publish', 'unpublish']
    
    @admin.action(description='Publish selected publications')
    def publish(self, request, queryset):
        queryset.update(is_published=True)
    
    @admin.action(description='Unpublish selected publications')
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(PublicationRevision)
class PublicationRevisionAdmin(admin.ModelAdmin):
    list_display = ('publication', 'version', 'created_at')
    list_filter = ('publication',)
    search_fields = ('publication__title', 'title')
    raw_id_fields = ('publication',)
    readonly_fields = ('publication', 'version', 'title', 'content', 'created_at')

