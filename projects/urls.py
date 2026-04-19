from django.urls import path
from . import views
from . import feeds

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('feed/', feeds.LatestProjectsFeed(), name='feed'),
    path('submit/', views.ProjectSubmitView.as_view(), name='create_manual'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.ProjectUpdateView.as_view(), name='edit'),
    path('<slug:slug>/fb-post/', views.ProjectPostFacebookView.as_view(), name='fb_post'),
]
