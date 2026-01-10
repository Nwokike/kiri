from django.urls import path
from . import views

app_name = 'publications'

urlpatterns = [
    path('', views.PublicationListView.as_view(), name='list'),
    path('<slug:slug>/', views.PublicationDetailView.as_view(), name='detail'),
]
