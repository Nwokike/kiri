from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='create_manual'),
    path('new/', views.ImportLandingView.as_view(), name='create'),
    path('api/repo-files/', views.RepoFilesApiView.as_view(), name='api_repo_files'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]
