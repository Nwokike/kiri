from django.urls import path
from . import views

app_name = 'publications'

urlpatterns = [
    path('', views.PublicationListView.as_view(), name='list'),
    path('submit/', views.PublicationCreateView.as_view(), name='create_manual'),
    path('new/', views.PublicationImportLandingView.as_view(), name='create'),
    path('<slug:slug>/edit/', views.PublicationUpdateView.as_view(), name='update'),
    path('<slug:slug>/', views.PublicationDetailView.as_view(), name='detail'),
]
