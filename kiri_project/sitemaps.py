"""
Django sitemap configuration for SEO.
Add to urls.py: path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from projects.models import Project
from publications.models import Publication


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return ['core:home', 'core:about']
    
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


# Register sitemaps for urls.py
sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'publications': PublicationSitemap,
}
