from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('json-formatter/', views.json_formatter, name='json_formatter'),
    path('regex-tester/', views.regex_tester, name='regex_tester'),
    path('base64/', views.base64_converter, name='base64_converter'),
    path('diff/', views.diff_viewer, name='diff_viewer'),
]
