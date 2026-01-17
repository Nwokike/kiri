"""
Django app configuration for Hugging Face provider.
"""
from django.apps import AppConfig


class HuggingFaceProviderConfig(AppConfig):
    name = "users.providers.huggingface"
    verbose_name = "Hugging Face OAuth Provider"
    default = True
    
    def ready(self):
        # Register the provider with allauth
        from allauth.socialaccount.providers import registry
        from .provider import HuggingFaceProvider
        
        # Only register if not already registered
        try:
            registry.get_class(HuggingFaceProvider.id)
        except KeyError:
            registry.register(HuggingFaceProvider)
