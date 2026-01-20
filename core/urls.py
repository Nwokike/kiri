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
    path('playground/', views.playground, name='playground'),
    path('comment/add/<int:content_type_id>/<int:object_id>/', views.add_comment, name='add_comment'),
    # Favorites
    path('favorites/', views.favorites_list, name='favorites'),
    path('favorites/toggle/<int:content_type_id>/<int:object_id>/', views.toggle_favorite, name='toggle_favorite'),
    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]



