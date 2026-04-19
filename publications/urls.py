from django.urls import path
from . import views

app_name = 'publications'

urlpatterns = [
    path('', views.PublicationListView.as_view(), name='list'),
    path('sync/', views.PublicationSyncView.as_view(), name='sync'),
    path('<slug:slug>/', views.PublicationDetailView.as_view(), name='detail'),
    path('<slug:slug>/delete/', views.PublicationDeleteView.as_view(), name='delete'),
    path('<slug:slug>/fb-post/', views.PublicationPostFacebookView.as_view(), name='fb_post'),
]
