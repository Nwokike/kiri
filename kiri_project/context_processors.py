"""
Custom context processors for Kiri templates.
"""
import os


def kiri_settings(request):
    """
    Inject Kiri-specific settings into all templates.
    """
    from django.utils import timezone
    return {
        'GOOGLE_ANALYTICS_ID': os.environ.get('GOOGLE_ANALYTICS_ID', ''),
        'SITE_URL': os.environ.get('SITE_URL', 'https://kiri.ng'),
        'CURRENT_YEAR': timezone.now().year,
    }


def ecosystem_platforms(request):
    """
    Inject active ecosystem platforms into all templates.
    Cached for 5 minutes to avoid repeated DB queries.
    """
    from django.core.cache import cache
    
    cache_key = 'ecosystem_platforms_active'
    platforms = cache.get(cache_key)
    if platforms is None:
        from core.models import EcosystemPlatform
        platforms = list(
            EcosystemPlatform.objects.filter(is_active=True)
            .values('name', 'url', 'icon_class', 'short_description')
        )
        cache.set(cache_key, platforms, 300)
    return {'ecosystem_platforms': platforms}


def active_projects(request):
    """
    Inject active projects into all templates for sidebar navigation.
    Cached for 5 minutes.
    """
    from django.core.cache import cache
    
    cache_key = 'active_projects_sidebar'
    projects = cache.get(cache_key)
    if projects is None:
        from projects.models import Project
        projects = list(
            Project.objects.filter(status=Project.Status.ACTIVE)
            .values('name', 'slug')
            .order_by('-created_at')[:5]  # Limit to 5 or so to avoid huge sidebar, they can still go to the Project page for more
        )
        cache.set(cache_key, projects, 300)
    return {'active_projects': projects}
