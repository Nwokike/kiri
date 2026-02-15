import markdown
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def render_markdown(value):
    """
    Renders markdown to HTML with nh3 sanitization.
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
        'a': {'href', 'title', 'target'},
        'img': {'src', 'alt', 'title'},
        'code': {'class'},
        '*': {'class'}
    }
    
    # Define allowed protocols
    allowed_protocols = ['http', 'https', 'mailto']
    
    # Sanitize
    cleaned_html = nh3.clean(
        html_content, 
        tags=set(allowed_tags), 
        attributes=allowed_attributes,
        url_schemes=set(allowed_protocols)
    )
    
    return mark_safe(cleaned_html)
