from django.urls import path
from . import views
from . import feeds

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('feed/', feeds.LatestProjectsFeed(), name='feed'),
    path('submit/', views.ProjectSubmitView.as_view(), name='create_manual'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]
