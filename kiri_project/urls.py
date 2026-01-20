from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("", include("pwa.urls")),
    
    # Main Routes
    path("library/", include("publications.urls", namespace="publications")),
    path("projects/", include("projects.urls", namespace="projects")),
    path("nexus/", include("users.urls", namespace="users")),
    path("tools/", include("tools.urls", namespace="tools")),
    path("discuss/", include("discussions.urls", namespace="discussions")),
    path("feed/", include("activity.urls", namespace="activity")),
    
    # Core (Home, About, etc.) - Must be last
    path("", include("core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

