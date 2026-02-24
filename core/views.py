from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, login_not_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Case, When, Value, IntegerField
from django.core.cache import cache
import nh3
from .models import ErrorLog


@login_not_required
def home(request):
    """Homepage with dynamic content from database."""
    from projects.models import Project
    from django.db.models import Count, Sum

    # Featured projects - prioritize HOT, then sort by stars
    featured_projects = Project.objects.filter(
        is_approved=True
    ).annotate(
        is_hot_order=Case(
            When(is_hot=True, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('is_hot_order', '-stars_count').select_related('submitted_by')[:6]

    # Dynamic stats
    approved = Project.objects.filter(is_approved=True)
    star_sum = approved.aggregate(total=Sum('stars_count'))['total'] or 0
    stats = {
        'total_projects': approved.count(),
        'total_stars': f"{star_sum:,}",
        'total_tools': 30,
    }

    # Project categories with counts
    categories = approved.values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:8]

    # Trending projects (most viewed)
    trending_projects = approved.order_by('-view_count')[:5]

    # Latest projects
    latest_projects = approved.order_by('-created_at')[:4]

    return render(request, "home.html", {
        "featured_projects": featured_projects,
        "stats": stats,
        "categories": categories,
        "trending_projects": trending_projects,
        "latest_projects": latest_projects,
    })


@login_not_required
def about(request):
    """About page."""
    return render(request, "core/about.html")






@login_not_required
def privacy(request):
    """Privacy policy page."""
    return render(request, "core/privacy.html")


@login_not_required
def terms(request):
    """Terms of service page."""
    return render(request, "core/terms.html")


@login_not_required
def contact(request):
    """Contact page with static information."""
    return render(request, "core/contact.html")


@login_not_required
def offline(request):
    """Offline page for PWA."""
    return render(request, "offline.html")


@login_not_required
def refund_policy(request):
    """Refund policy page."""
    return render(request, "core/refund.html")


@login_not_required
def health(request):
    """Health check endpoint for deployment verification."""
    return JsonResponse({
        "status": "ok",
        "service": "kiri",
    })


@login_not_required
def serviceworker(request):
    """
    Serve serviceworker.js with a robust static file resolver.
    This prevents 500 errors if the static manifest is out of sync.
    """
    from django.templatetags.static import static
    from django.contrib.staticfiles.storage import staticfiles_storage

    def safe_static(path):
        try:
            return static(path)
        except ValueError:
            # Fallback to the raw STATIC_URL + path if manifest entry is missing
            from django.conf import settings
            return f"{settings.STATIC_URL}{path}"

    context = {
        "static": safe_static
    }
    
    # We use a custom context to override the 'static' tag behavior in the template
    # if we were using it as a tag, but here we can just pass it as a variable 
    # and use {{ static("...") }} in the JS template.
    # However, since serviceworker.js uses {% load static %}, we actually need
    # to handle this in the view OR use a custom template tag.
    # A simpler way is to just use a try/except in the view if the template
    # engine allows, but it's easier to just fix the template.
    
    try:
        response = render(request, "serviceworker.js", context)
        response['Content-Type'] = 'application/javascript'
        return response
    except Exception as e:
        # Absolute fallback for production stability
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Service Worker rendering failed: {e}")
        return HttpResponse("// Service Worker unavailable due to configuration error", content_type="application/javascript")


@login_not_required
def pwa_manifest(request):
    """
    Serve manifest.json from settings with login_not_required.
    """
    from django.conf import settings
    manifest = {
        "name": getattr(settings, "PWA_APP_NAME", "Kiri"),
        "short_name": getattr(settings, "PWA_APP_SHORT_NAME", "Kiri"),
        "description": getattr(settings, "PWA_APP_DESCRIPTION", ""),
        "start_url": getattr(settings, "PWA_APP_START_URL", "/"),
        "display": getattr(settings, "PWA_APP_DISPLAY", "standalone"),
        "background_color": getattr(settings, "PWA_APP_BACKGROUND_COLOR", "#FFFFFF"),
        "theme_color": getattr(settings, "PWA_APP_THEME_COLOR", "#000000"),
        "orientation": getattr(settings, "PWA_APP_ORIENTATION", "any"),
        "scope": getattr(settings, "PWA_APP_SCOPE", "/"),
        "icons": getattr(settings, "PWA_APP_ICONS", []),
    }
    return JsonResponse(manifest)


@login_not_required
def silent_asset(request, filename):
    """
    Silently serve an empty response for missing assets (like stackframe.js)
    to keep logs clean.
    """
    return HttpResponse("", content_type="application/javascript")



