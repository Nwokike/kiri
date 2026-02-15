from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('@<str:username>/', views.UserProfileDetailView.as_view(), name='profile'),
    path('settings/integrations/', views.IntegrationsView.as_view(), name='integrations'),
    path('follow/<str:username>/', views.follow_user, name='follow'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow'),
]

