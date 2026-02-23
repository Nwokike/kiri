from django.urls import path
from . import views
from . import api

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='create_manual'), 
    path('new/', views.ImportLandingView.as_view(), name='create'), 
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
    path('api/user-repos/', api.user_repos_api, name='api_user_repos'),
    path('api/repo-files/', api.repo_files_api, name='api_repo_files'),
]