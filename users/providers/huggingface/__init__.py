"""
Hugging Face OAuth2/OIDC Provider for django-allauth.
"""
# Don't import the provider here to avoid circular imports during app loading
# The provider is registered via the apps.py ready() method
