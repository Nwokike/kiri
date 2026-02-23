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
        'ADSENSE_CLIENT_ID': os.environ.get('ADSENSE_CLIENT_ID', ''),
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
