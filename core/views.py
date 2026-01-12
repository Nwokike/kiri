from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from .models import Comment
from .forms import CommentForm


def home(request):
    """Homepage with dynamic content from database."""
    from projects.models import Project
    from publications.models import Publication

    # Get featured projects (approved, ordered by stars) - 'HOT' logic replaces featured
    hot_projects = Project.objects.filter(is_approved=True, is_hot=True).order_by('-stars_count')[:6]
    if not hot_projects:
         # Fallback to stars if no HOT projects
         hot_projects = Project.objects.filter(is_approved=True).order_by('-stars_count')[:6]

    # Get latest publications
    latest_publications = Publication.objects.filter(is_published=True).order_by('-created_at')[:3]

    return render(request, "home.html", {
        "featured_projects": hot_projects,
        "latest_publications": latest_publications,
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
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.content_object = obj
        
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id)
            comment.parent = parent
            
        comment.save()
        
        # Return the new comment rendered as HTML (for appending)
        return render(request, 'core/partials/comment_item.html', {'comment': comment})
    
    return HttpResponseForbidden("Invalid Form")
