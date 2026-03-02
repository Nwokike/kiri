from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:tool_slug>/', views.tool_detail, name='tool_detail'),
]
