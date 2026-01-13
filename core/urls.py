from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('offline/', views.offline, name='offline'),
    path('health/', views.health, name='health'),
    path('comment/add/<int:content_type_id>/<int:object_id>/', views.add_comment, name='add_comment'),
]
