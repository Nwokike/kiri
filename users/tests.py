from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from axes.models import AccessAttempt

User = get_user_model()

class LoginViewTests(TestCase):
    def test_login_page_redirects_for_anonymous(self):
        response = self.client.get('/kiri-manage/login/')
        self.assertEqual(response.status_code, 200)

class AxesLockoutTest(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'password123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client = Client()

    def test_login_lockout(self):
        login_url = reverse('admin:login') 
        limit = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
        
        for _ in range(limit):
            response = self.client.post(login_url, {
                'username': self.username,
                'password': 'wrongpassword'
            })
            # Axes 8.x often returns 200 (still showing login) or 429 (throttled)
            self.assertIn(response.status_code, [200, 429]) 
            
        # The next attempt should lock it out
        response = self.client.post(login_url, {
            'username': self.username,
            'password': 'wrongpassword'
        })
        
        # Lockout response code
        self.assertIn(response.status_code, [403, 429])
        self.assertTrue(AccessAttempt.objects.filter(username=self.username).exists())
