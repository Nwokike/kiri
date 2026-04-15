from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_not_required
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth import views as auth_views
from core import views as core_views
from .sitemaps import sitemaps

urlpatterns = [
    # Admin at obscure path
    path("kiri-manage/", admin.site.urls),

    # Authentication (Django built-in)
    path("accounts/login/", login_not_required(auth_views.LoginView.as_view(
        template_name="registration/login.html",
    )), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Icon
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True)),

    # Suppress noisy dev tool requests
    path(".well-known/appspecific/com.chrome.devtools.json", core_views.silent_asset, {'filename': 'devtools.json'}),

    # SEO
    path("sitemap.xml", login_not_required(sitemap), {'sitemaps': sitemaps}, name='sitemap'),
    path("robots.txt", login_not_required(TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))),

    # Main Routes
    path("projects/", include("projects.urls", namespace="projects")),
    path("tools/", include("tools.urls", namespace="tools")),
    path("publications/", include("publications.urls", namespace="publications")),

    # Core (Home, About, etc.) - Must be last
    path("", include("core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
