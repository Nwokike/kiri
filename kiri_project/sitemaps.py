"""
Django sitemap configuration for SEO.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.models import Project


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages and tools."""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return [
            # Core
            'core:home', 'core:about', 'core:contact', 'core:privacy', 'core:terms', 'core:refund_policy',
            'projects:list', 'tools:index',
            
            # Tools: Programming & Utilities
            'tools:sql_workbench', 'tools:json_formatter', 'tools:regex_tester', 'tools:base64_converter',
            'tools:diff_viewer', 'tools:url_encoder', 'tools:timestamp_converter',
            'tools:hash_generator', 'tools:uuid_generator', 'tools:sql_refinery',
            'tools:cron_generator', 'tools:jwt_parser',
            'tools:latex_editor', 'tools:image_to_base64', 'tools:yaml_json_converter',
            'tools:json_csv_converter', 'tools:markdown_previewer', 'tools:html_entities',
            'tools:api_tester', 'tools:data_profiler',
            'tools:json_schema_validator',
            
            # Tools: Media & Docs
            'tools:pdf_editor',
            'tools:markdown_to_pdf',
            'tools:image_to_pdf',
            'tools:pdf_to_image',
       
            'tools:pdf_splitter',
            'tools:pdf_merger',
            'tools:pdf_text_extractor',
            'tools:exif_viewer',
            'tools:qr_generator',
            'tools:ocr_tool',
            'tools:audio_transcriber',
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
        
    def location(self, obj):
        return reverse('projects:detail', kwargs={'slug': obj.slug})


# Register sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
}