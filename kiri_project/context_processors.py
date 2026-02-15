"""
Custom context processors for Kiri templates.
"""
import os


def kiri_settings(request):
    """
    Inject Kiri-specific settings into all templates.
    """
    return {
        'GOOGLE_ANALYTICS_ID': os.environ.get('GOOGLE_ANALYTICS_ID', ''),
        'ADSENSE_CLIENT_ID': os.environ.get('ADSENSE_CLIENT_ID', ''),
        'SITE_URL': os.environ.get('SITE_URL', 'https://kiri.ng'),
    }
