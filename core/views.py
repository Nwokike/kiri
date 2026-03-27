from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache


@login_not_required
def home(request):
    """Homepage with dynamic content from database. Cached for 5 minutes."""
    context = cache.get('homepage_context')
    if context is None:
        from projects.models import Project
        from django.db.models import Count, Sum

        all_projects = Project.objects.all()

        # Featured projects (manually flagged), then by most recent
        featured_projects = list(
            all_projects.filter(is_featured=True).order_by('-created_at')[:6]
        )

        # Dynamic stats
        stats = {
            'total_projects': all_projects.count(),
            'total_live': all_projects.exclude(live_url='').count(),
        }

        # Dynamic tool count from registry
        try:
            from tools.registry import TOOLS
            stats['total_tools'] = len(TOOLS)
        except ImportError:
            stats['total_tools'] = 30

        # Categories with counts
        categories = list(
            all_projects.values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )

        # Latest projects
        latest_projects = list(all_projects.order_by('-created_at')[:5])

        context = {
            "featured_projects": featured_projects,
            "stats": stats,
            "categories": categories,
            "latest_projects": latest_projects,
        }
        cache.set('homepage_context', context, 300)

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
def silent_asset(request, filename):
    """Silently serve empty response for missing assets to keep logs clean."""
    content_type = "application/json" if filename.endswith(".json") else "application/javascript"
    return HttpResponse("", content_type=content_type)
