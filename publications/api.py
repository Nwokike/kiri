from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.text import slugify
from .models import Publication
import json
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def studio_publish(request):
    """
    Creates a new Publication directly from Kiri Studio.
    Expects JSON: { title, content, script_content (optional), repo_url (optional) }
    """
    try:
        data = json.loads(request.body)
        title = data.get('title')
        content = data.get('content') # Markdown text
        script_content = data.get('script_content', '')
        repo_url = data.get('repo_url', '')
        
        if not title or not content:
            return JsonResponse({"error": "Title and content are required."}, status=400)
            
        # Create Slug
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Publication.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        # Determine category (heuristic)
        category = 'research' # Default
        if 'tutorial' in title.lower(): category = 'tutorial'
        if 'analysis' in title.lower(): category = 'data_science'
        
        publication = Publication.objects.create(
            title=title,
            slug=slug,
            author=request.user,
            content=content,
            status='draft', # Start as draft for safety
            category=category,
            github_repo_url=repo_url,
            # We assume you might add an 'executable_script' field to Publication model later 
            # or append it to content. For now, let's append it as a code block if present.
        )
        
        if script_content:
            publication.content += f"\n\n## Source Code\n```python\n{script_content}\n```"
            publication.save()
            
        return JsonResponse({
            "status": "success",
            "message": "Draft created successfully!",
            "url": publication.get_absolute_url()
        })

    except Exception as e:
        logger.error(f"Studio Publish Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)