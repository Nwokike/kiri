"""
Hugging Face OAuth2 Views.

Implements the adapter that connects to Hugging Face's OAuth2/OIDC endpoints.
"""
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .provider import HuggingFaceProvider


class HuggingFaceOAuth2Adapter(OAuth2Adapter):
    """OAuth2 adapter for Hugging Face."""
    
    provider_id = HuggingFaceProvider.id
    
    # Hugging Face OAuth2/OIDC endpoints
    authorize_url = "https://huggingface.co/oauth/authorize"
    access_token_url = "https://huggingface.co/oauth/token"
    profile_url = "https://huggingface.co/oauth/userinfo"
    
    def complete_login(self, request, app, token, **kwargs):
        """Complete the login process by fetching user info."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Accept": "application/json",
        }
        
        response = requests.get(self.profile_url, headers=headers, timeout=15)
        response.raise_for_status()
        extra_data = response.json()
        
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(HuggingFaceOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(HuggingFaceOAuth2Adapter)
