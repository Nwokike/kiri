"""
Hugging Face OAuth2 URL configuration.
"""
from django.urls import path

from .views import oauth2_callback, oauth2_login

from django.contrib.auth.decorators import login_not_required

urlpatterns = [
    path("login/", login_not_required(oauth2_login), name="huggingface_login"),
    path("login/callback/", login_not_required(oauth2_callback), name="huggingface_callback"),
]
