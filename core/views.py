from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Case, When, Value, IntegerField
from django.core.cache import cache
import bleach
from .models import Comment
from .forms import CommentForm


def home(request):
    """Homepage with dynamic content from database."""
    from projects.models import Project
    from publications.models import Publication

    # Get featured projects - prioritize HOT, then sort by stars (single optimized query)
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


def health(request):
    """Health check endpoint for deployment verification."""
    return JsonResponse({
        "status": "ok",
        "service": "kiri",
    })


def universal_translator(request):
    return render(request, "demos/universal_translator.html")

def serviceworker(request):
    response = render(request, "serviceworker.js")
    response['Content-Type'] = 'application/javascript'
    return response


@login_required
@require_POST
def add_comment(request, content_type_id, object_id):
    """
    HTMX View to add a comment.
    """
    content_type = get_object_or_404(ContentType, id=content_type_id)
    obj = get_object_or_404(content_type.model_class(), id=object_id)
    
    # Rate Limiting (30s cooldown)
    cache_key = f"comment_rate_{request.user.id}"
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
        cache.set(cache_key, True, 30)
        
        # Return the new comment rendered as HTML (for appending)
        return render(request, 'core/partials/comment_item.html', {'comment': comment})
    
    # Return errors for HTMX to display
    return render(request, 'core/partials/comment_form_errors.html', {
        'errors': form.errors
    }, status=400)
