from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health, name='health'),
    path('demo/universal-translator/', views.universal_translator, name='universal_translator'),
    path('comment/add/<int:content_type_id>/<int:object_id>/', views.add_comment, name='add_comment'),
]
