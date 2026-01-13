from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("serviceworker.js", core_views.serviceworker, name="serviceworker"),
    path("", include("pwa.urls")),
    
    # Main Routes
    path("library/", include("publications.urls", namespace="publications")),
    path("projects/", include("projects.urls", namespace="projects")),
    path("nexus/", include("users.urls", namespace="users")),
    
    # Core (Home, About, etc.) - Must be last
    path("", include("core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
