"""
Django sitemap configuration for SEO.
Add to urls.py: path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from projects.models import Project
from publications.models import Publication


from discussions.models import Topic


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return [
            'core:home', 'core:about', 
            'publications:list', 'projects:list', 'discussions:list', 'tools:index',
            'tools:json_formatter', 'tools:regex_tester', 'tools:base64_converter',
            'tools:diff_viewer', 'tools:url_encoder', 'tools:timestamp_converter',
            'tools:hash_generator', 'tools:uuid_generator', 'tools:sql_formatter',
            'tools:cron_generator', 'tools:jwt_parser', 'tools:unit_converter',
            'tools:latex_editor', 'tools:json_to_csv', 'tools:image_to_base64',
            'tools:yaml_json_converter', 'tools:markdown_previewer', 'tools:html_entities',
            'tools:password_generator', 'tools:api_tester', 'tools:data_profiler',
            'tools:json_schema_validator'
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


class PublicationSitemap(Sitemap):
    """Sitemap for publication pages."""
    changefreq = 'monthly'
    priority = 0.7
    
    def items(self):
        return Publication.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at


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


# Register sitemaps for urls.py
sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'publications': PublicationSitemap,
    'discussions': TopicSitemap,
}
