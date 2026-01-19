from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Case, When, Value, IntegerField
from django.core.cache import cache
import bleach
from .models import Comment, Favorite, Notification
from .forms import CommentForm


def home(request):
    """Homepage with dynamic content from database."""
    from projects.models import Project
    from publications.models import Publication

    # Get featured projects - prioritize HOT, then sort by stars
    featured_projects = Project.objects.filter(
        is_approved=True
    ).annotate(
        is_hot_order=Case(
            When(is_hot=True, then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('is_hot_order', '-stars_count').select_related('submitted_by')[:6]

    # Get latest publications
    latest_publications = Publication.objects.filter(
        is_published=True
    ).order_by('-created_at').select_related('author')[:3]

    return render(request, "home.html", {
        "featured_projects": featured_projects,
        "latest_publications": latest_publications,
    })


def about(request):
    """About page."""
    return render(request, "core/about.html")


def privacy(request):
    """Privacy policy page."""
    return render(request, "core/privacy.html")


def terms(request):
    """Terms of service page."""
    return render(request, "core/terms.html")


def offline(request):
    """Offline page for PWA."""
    return render(request, "offline.html")


def health(request):
    """Health check endpoint for deployment verification."""
    return JsonResponse({
        "status": "ok",
        "service": "kiri",
    })


def serviceworker(request):
    response = render(request, "serviceworker.js")
    response['Content-Type'] = 'application/javascript'
    return response


@login_required
@require_POST
def add_comment(request, content_type_id, object_id):
    """HTMX View to add a comment."""
    content_type = get_object_or_404(ContentType, id=content_type_id)
    obj = get_object_or_404(content_type.model_class(), id=object_id)
    
    # Rate Limiting (30s cooldown)
    from django.conf import settings
    is_testing = getattr(settings, 'TESTING', False)
    cache_key = f"comment_rate_{request.user.id}"
    
    if not is_testing:
        if cache.get(cache_key):
            return HttpResponse("Please wait before commenting again.", status=429)

    form = CommentForm(request.POST) 
    if form.is_valid():
        comment = form.save(commit=False)
        
        # Sanitize Content
        comment.content = bleach.clean(
            comment.content,
            tags=['b', 'i', 'code', 'pre', 'strong', 'em'],
            attributes={},
            strip=True
        )
        
        comment.author = request.user
        comment.content_object = obj
        
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent
            
        comment.save()
        
        # Set rate limit
        if not is_testing:
            cache.set(cache_key, True, 30)
        
        # Return the new comment rendered as HTML
        return render(request, 'core/partials/comment_item.html', {'comment': comment})
    
    # Return errors for HTMX to display
    return render(request, 'core/partials/comment_form_errors.html', {
        'errors': form.errors
    }, status=400)


# ============================================================================
# FAVORITES
# ============================================================================

@login_required
def favorites_list(request):
    """Display user's favorited items."""
    from django.contrib.contenttypes.prefetch import GenericPrefetch
    from projects.models import Project
    from publications.models import Publication
    
    project_ct = ContentType.objects.get_for_model(Project)
    pub_ct = ContentType.objects.get_for_model(Publication)
    
    # Use GenericPrefetch to avoid N+1 when accessing content_object
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('content_type').prefetch_related(
        GenericPrefetch(
            'content_object',
            [
                Project.objects.select_related('submitted_by'),
                Publication.objects.select_related('author'),
            ]
        )
    ).order_by('-created_at')
    
    project_favorites = [f for f in favorites if f.content_type_id == project_ct.id]
    publication_favorites = [f for f in favorites if f.content_type_id == pub_ct.id]
    
    return render(request, 'core/favorites.html', {
        'favorites': favorites,
        'project_favorites': project_favorites,
        'publication_favorites': publication_favorites,
    })


@login_required
@require_POST
def toggle_favorite(request, content_type_id, object_id):
    """Toggle favorite status for an item. HTMX compatible."""
    content_type = get_object_or_404(ContentType, id=content_type_id)
    obj = get_object_or_404(content_type.model_class(), id=object_id)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id,
    )
    
    if not created:
        # Already exists, remove it
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True
        # Queue GitHub star sync if user has repo scope
        try:
            from kiri_project.tasks import sync_github_star
            sync_github_star(favorite.id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to queue GitHub star sync: {e}")
    
    # Return updated button for HTMX
    return render(request, 'core/partials/favorite_button.html', {
        'obj': obj,
        'content_type': content_type,
        'is_favorited': is_favorited,
    })


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@login_required
def notifications_list(request):
    """Display user's notifications."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor').order_by('-created_at')[:50]
    
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'core/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    
    if request.htmx:
        return HttpResponse('')
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.htmx:
        return HttpResponse('<span class="text-sm text-[#6C757D]">All caught up!</span>')
    return JsonResponse({'status': 'ok'})

