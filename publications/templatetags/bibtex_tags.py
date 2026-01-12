from django import template

register = template.Library()

@register.filter
def bibtex_escape(value):
    """
    Escapes special characters for BibTeX/LaTeX.
    """
    if not value:
        return ""
        
    replacements = {
        '{': r'\{',
        '}': r'\}',
        '%': r'\%',
        '#': r'\#',
        '&': r'\&',
        '_': r'\_',
        '$': r'\$',
    }
    
    for char, escaped in replacements.items():
        value = str(value).replace(char, escaped)
    
    return value
