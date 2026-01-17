"""
Hugging Face OAuth2/OIDC Provider for django-allauth.

Hugging Face supports OpenID Connect, which is built on OAuth 2.0.
This provider implements the OAuth2 flow to authenticate users with Hugging Face.
"""
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class HuggingFaceAccount(ProviderAccount):
    """Hugging Face account representation."""
    
    def get_avatar_url(self):
        return self.account.extra_data.get("picture", "")
    
    def to_str(self):
        return self.account.extra_data.get("preferred_username", super().to_str())


class HuggingFaceProvider(OAuth2Provider):
    """Hugging Face OAuth2/OIDC Provider."""
    
    id = "huggingface"
    name = "Hugging Face"
    account_class = HuggingFaceAccount
    
    def get_default_scope(self):
        """Return default scopes for Hugging Face OAuth."""
        return ["openid", "profile", "email"]
    
    def extract_uid(self, data):
        """Extract user ID from Hugging Face response."""
        return str(data.get("sub") or data.get("id", ""))
    
    def extract_common_fields(self, data):
        """Extract common user fields from Hugging Face response."""
        return {
            "username": data.get("preferred_username", ""),
            "email": data.get("email", ""),
            "first_name": data.get("name", "").split()[0] if data.get("name") else "",
            "last_name": " ".join(data.get("name", "").split()[1:]) if data.get("name") else "",
        }
    
    def extract_email_addresses(self, data):
        """Extract email addresses from Hugging Face response."""
        email = data.get("email")
        if email:
            return [{"email": email, "verified": data.get("email_verified", False), "primary": True}]
        return []


provider_classes = [HuggingFaceProvider]
