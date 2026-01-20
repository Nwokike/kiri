from django.urls import path
from . import views
from .api import user_repos_api
from . import api

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='create_manual'), # Renamed for clarity but kept submit/ for URL compatibility
    path('new/', views.ImportLandingView.as_view(), name='create'), # New default "New Project" landing
    path('api/user-repos/', api.user_repos_api, name='api_user_repos'),
    path('api/repos/', api.user_repos_api, name='api_repos_legacy'), # Kept for compatibility if used elsewhere
    path('api/studio/gist/', api.save_gist_api, name='api_studio_gist'),
    path('api/studio/ai/', api.studio_ai_assist, name='api_studio_ai'),
    path('api/repo-files/', api.repo_files_api, name='api_repo_files'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]
