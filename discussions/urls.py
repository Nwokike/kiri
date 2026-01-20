from django.urls import path
from . import views

app_name = 'discussions'

urlpatterns = [
    path('', views.TopicListView.as_view(), name='list'),
    path('create/', views.TopicCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.TopicDetailView.as_view(), name='detail'),
]
