from django.shortcuts import render


def home(request):
    """Homepage with dynamic content from database."""
    from projects.models import Project
    from publications.models import Publication
    
    # Get featured projects (approved, ordered by stars)
    featured_projects = Project.objects.filter(is_approved=True).order_by('-stars_count')[:6]
    
    # Get latest publications
    latest_publications = Publication.objects.filter(is_published=True).order_by('-created_at')[:3]
    
    return render(request, "home.html", {
        "featured_projects": featured_projects,
        "latest_publications": latest_publications,
    })


def universal_translator(request):
    """Project 0: Universal Translator - Client-side ML translation with Transformers.js."""
    return render(request, "core/universal_translator.html")
