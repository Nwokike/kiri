from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.db.models import Case, When, Value, IntegerField


@login_not_required
def home(request):
    """Homepage with dynamic content from database. Cached for 5 minutes."""
    context = cache.get('homepage_context')
    if context is None:
        from projects.models import Project
        from django.db.models import Count, Sum

        # Featured projects - prioritize HOT, then sort by stars
        featured_projects = list(
            Project.objects.filter(is_approved=True)
            .annotate(
                is_hot_order=Case(
                    When(is_hot=True, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                )
            )
            .order_by('is_hot_order', '-stars_count')
            .select_related('submitted_by')[:6]
        )

        # Dynamic stats
        approved = Project.objects.filter(is_approved=True)
        star_sum = approved.aggregate(total=Sum('stars_count'))['total'] or 0

        # Dynamic tool count from registry
        try:
            from tools.registry import TOOLS
            tool_count = len(TOOLS)
        except ImportError:
            tool_count = 30

        stats = {
            'total_projects': approved.count(),
            'total_stars': f"{star_sum:,}",
            'total_tools': tool_count,
        }

        categories = list(
            approved.values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )
        trending_projects = list(approved.order_by('-view_count')[:5])
        latest_projects = list(approved.order_by('-created_at')[:4])

        context = {
            "featured_projects": featured_projects,
            "stats": stats,
            "categories": categories,
            "trending_projects": trending_projects,
            "latest_projects": latest_projects,
        }
        cache.set('homepage_context', context, 300)  # 5 minutes

    return render(request, "home.html", context)


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
    """Serve serviceworker.js with static file manifest fallback."""
    try:
        response = render(request, "serviceworker.js")
        response['Content-Type'] = 'application/javascript'
        return response
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Service Worker rendering failed: {e}")
        return HttpResponse(
            "// Service Worker unavailable",
            content_type="application/javascript",
        )


@login_not_required
def pwa_manifest(request):
    """Serve manifest.json from settings."""
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
    """Silently serve empty response for missing assets to keep logs clean."""
    content_type = "application/json" if filename.endswith(".json") else "application/javascript"
    return HttpResponse("", content_type=content_type)
