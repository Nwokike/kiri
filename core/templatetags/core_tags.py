from django import template
from django.contrib.contenttypes.models import ContentType

from functools import lru_cache

register = template.Library()

@lru_cache(maxsize=32)
def _get_ct_id(model_class):
    """Cached lookup for ContentType ID."""
    return ContentType.objects.get_for_model(model_class).id

@register.filter
def get_content_type_id(obj):
    """Returns the ContentType ID for a model instance."""
    if not obj:
        return None
    return _get_ct_id(type(obj))
