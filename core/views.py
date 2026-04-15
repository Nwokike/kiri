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
            all_projects.filter(is_featured=True).order_by('-created_at')[:8]
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
        
        # Latest publications
        from publications.models import Publication
        latest_publications = list(Publication.objects.order_by('-published_at')[:4])

        context = {
            "featured_projects": featured_projects,
            "stats": stats,
            "categories": categories,
            "latest_projects": latest_projects,
            "latest_publications": latest_publications,
        }
        cache.set('homepage_context', context, 300)

    return render(request, "home.html", context)


@login_not_required
def about(request):
    """About page."""
    from projects.models import Project
    active_projects = Project.objects.filter(status=Project.Status.ACTIVE).order_by('-is_featured', '-created_at')
    return render(request, "core/about.html", {"projects": active_projects})


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


@login_not_required
def global_search(request):
    """
    Unified JSON API endpoint for 'Spotlight' search.
    Aggregates Projects, Publications, and Tools.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({"results": []})
        
    results = []
    
    # 1. Projects
    from projects.models import Project
    projects = Project.objects.filter(status=Project.Status.ACTIVE, name__icontains=query)[:5]
    for p in projects:
        results.append({
            "type": "Project",
            "title": p.name,
            "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
            "url": p.get_absolute_url(),
            "icon": "fa-diagram-project"
        })
        
    # 2. Publications
    from publications.models import Publication
    pubs = Publication.objects.filter(title__icontains=query)[:5]
    for pub in pubs:
        results.append({
            "type": "Publication",
            "title": pub.title,
            "description": pub.description[:100] + "..." if len(pub.description) > 100 else pub.description,
            "url": pub.get_absolute_url(),
            "icon": "fa-book"
        })
        
    # 3. Tools
    try:
        from tools.registry import TOOLS
        from django.urls import reverse
        for tool_id, tool_data in TOOLS.items():
            if query.lower() in tool_data['name'].lower() or query.lower() in tool_data.get('description', '').lower():
                results.append({
                    "type": "Tool",
                    "title": tool_data['name'],
                    "description": tool_data.get('description', '')[:100] + "..." if len(tool_data.get('description', '')) > 100 else tool_data.get('description', ''),
                    "url": reverse('tools:tool_detail', args=[tool_id]),
                    "icon": tool_data.get('icon', 'fa-toolbox')
                })
    except ImportError:
        pass
        
    return JsonResponse({"results": results[:15]})
