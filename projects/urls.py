from django.urls import path
from . import views
from .api import user_repos_api

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='submit'),
    path('api/repos/', user_repos_api, name='user_repos_api'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]

