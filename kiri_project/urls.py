from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("pwa.urls")),
    
    # Districts
    path("library/", include("publications.urls", namespace="publications")),
    path("colosseum/", include("projects.urls", namespace="projects")),
    
    # Core (Home, About, etc.) - Must be last to catch catch-all paths if any
    path("", include("core.urls", namespace="core")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
