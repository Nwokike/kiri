from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_not_required
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView, RedirectView
from core import views as core_views
from .sitemaps import sitemaps

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/signup/", RedirectView.as_view(url="/accounts/login/", permanent=True)),
    path("accounts/", include("allauth.urls")),
    path("accounts/huggingface/", include("users.providers.huggingface.urls")),
    path("serviceworker.js", core_views.serviceworker, name="serviceworker"),
    path("manifest.json", core_views.pwa_manifest, name="pwa_manifest"),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True)),
    path("studio/stackframe.js", core_views.silent_asset, {'filename': 'stackframe.js'}),
    path(".well-known/appspecific/com.chrome.devtools.json", core_views.silent_asset, {'filename': 'devtools.json'}),
    path("sitemap.xml", login_not_required(sitemap), {'sitemaps': sitemaps}, name='sitemap'),
    path("robots.txt", login_not_required(TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))),
    path("", include("pwa.urls")),
    
    # Main Routes
    path("projects/", include("projects.urls", namespace="projects")),
    path("tools/", include("tools.urls", namespace="tools")),
    
    # Core (Home, About, etc.) - Must be last
    path("", include("core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

