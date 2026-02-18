"""
Django sitemap configuration for SEO.
Add to urls.py: 
from django.contrib.sitemaps.views import sitemap
from .sitemaps import sitemaps
path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.contrib.auth import get_user_model

from projects.models import Project
from publications.models import Publication
from discussions.models import Topic

class StaticViewSitemap(Sitemap):
    """Sitemap for static pages and tools."""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return [
            # Core
            'core:home', 'core:about', 'core:contact', 'core:privacy', 'core:terms', 'core:refund_policy',
            'publications:list', 'projects:list', 'discussions:list', 'tools:index',
            
            # Tools: Programming & Utilities
            'tools:sql_workbench', 'tools:json_formatter', 'tools:regex_tester', 'tools:base64_converter',
            'tools:diff_viewer', 'tools:url_encoder', 'tools:timestamp_converter',
            'tools:hash_generator', 'tools:uuid_generator', 'tools:sql_refinery',
            'tools:cron_generator', 'tools:jwt_parser', 'tools:unit_converter',
            'tools:latex_editor', 'tools:image_to_base64', 'tools:yaml_json_converter',
            'tools:json_csv_converter', 'tools:markdown_previewer', 'tools:html_entities',
            'tools:password_generator', 'tools:api_tester', 'tools:data_profiler',
            'tools:json_schema_validator',
            
            # Tools: Media & Docs (The New Suite)
            'tools:pdf_editor',
            'tools:markdown_to_pdf',
            'tools:image_to_pdf',
            'tools:pdf_to_image',
            'tools:pdf_splitter',
            'tools:pdf_merger',          # Added
            'tools:pdf_text_extractor',  # Added
            'tools:heic_to_jpg',
            'tools:image_compressor',
            'tools:image_converter',     # Added
            'tools:image_resizer',       # Added
            'tools:exif_viewer',
            'tools:qr_generator',
            'tools:ocr_tool',
            'tools:audio_transcriber'
        ]
    
    def location(self, item):
        return reverse(item)

class ProjectSitemap(Sitemap):
    """Sitemap for project pages."""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Project.objects.filter(is_approved=True)
    
    def lastmod(self, obj):
        return obj.updated_at
        
    # Optional: If your model has get_absolute_url, you can remove this
    def location(self, obj):
        return reverse('projects:detail', kwargs={'slug': obj.slug})

class PublicationSitemap(Sitemap):
    """Sitemap for publication pages."""
    changefreq = 'monthly'
    priority = 0.7
    
    def items(self):
        return Publication.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('publications:detail', kwargs={'slug': obj.slug})

class TopicSitemap(Sitemap):
    """Sitemap for discussion topics."""
    changefreq = 'daily'
    priority = 0.6
    
    def items(self):
        return Topic.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('discussions:detail', kwargs={'slug': obj.slug})

class UserSitemap(Sitemap):
    """Sitemap for public user profiles."""
    changefreq = 'weekly'
    priority = 0.6
    
    def items(self):
        User = get_user_model()
        # Ensure your User model actually has 'is_profile_public' field
        if hasattr(User, 'is_profile_public'):
            return User.objects.filter(is_active=True, is_profile_public=True)
        return User.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        # Fallback if updated_at doesn't exist on User
        return getattr(obj, 'date_joined', None)

    def location(self, obj):
        return reverse('users:profile', kwargs={'username': obj.username})

# Register sitemaps for urls.py
sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'publications': PublicationSitemap,
    'discussions': TopicSitemap,
    'users': UserSitemap,
}