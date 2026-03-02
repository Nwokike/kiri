"""
Django sitemap configuration for SEO.
Auto-generates tool URLs from tools/urls.py to stay in sync.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.models import Project


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages and tools."""
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        # Core pages
        pages = [
            'core:home', 'core:about', 'core:contact',
            'core:privacy', 'core:terms', 'core:refund_policy',
            'projects:list', 'tools:index',
        ]

        # Auto-discover tool URLs from tools/registry.py
        try:
            from tools.registry import TOOLS
            for slug in TOOLS.keys():
                pages.append(('tools:tool_detail', {'tool_slug': slug}))
        except ImportError:
            pass

        return pages

    def location(self, item):
        if isinstance(item, tuple):
            return reverse(item[0], kwargs=item[1])
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


sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
}