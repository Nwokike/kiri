import markdown
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def render_markdown(value):
    """
    Renders markdown to HTML with bleach sanitization.
    """
    if not value:
        return ""
        
    # Convert markdown to HTML
    html_content = markdown.markdown(
        value, 
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    # Define allowed tags and attributes
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre', 
        'blockquote', 'a', 'img', 'br', 'hr', 'table', 'thead', 
        'tbody', 'tr', 'th', 'td'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title'],
        'code': ['class'],
        '*': ['class']
    }
    
    # Sanitize
    cleaned_html = bleach.clean(
        html_content, 
        tags=allowed_tags, 
        attributes=allowed_attributes,
        strip=True
    )
    
    return mark_safe(cleaned_html)
