from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('refund/', views.refund_policy, name='refund_policy'),
    
    # --- New Studio Routes ---
    path('studio/py/', views.studio_py, name='studio_py'), # PyStudio
    path('studio/js/', views.studio_js, name='studio_js'), # JS Studio
    
    # Notifications & Favorites
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear/', views.mark_all_notifications_read, name='clear_notifications'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('favorite/toggle/<int:content_type_id>/<int:object_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # Comments
    path('comments/post/<int:content_type_id>/<int:object_id>/', views.add_comment, name='post_comment'),
    # path('comments/delete/<int:pk>/', views.delete_comment, name='delete_comment'), # Missing in views.py
]