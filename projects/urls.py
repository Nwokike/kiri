from django.urls import path
from . import views
from .api import user_repos_api
from . import api

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='submit'),
    path('api/repos/', api.user_repos_api, name='api_repos'),
    path('api/studio/gist/', api.save_gist_api, name='api_studio_gist'),
    path('api/studio/ai/', api.studio_ai_assist, name='api_studio_ai'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]
