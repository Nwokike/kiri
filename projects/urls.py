from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('submit/', views.ProjectSubmitView.as_view(), name='submit'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
]
