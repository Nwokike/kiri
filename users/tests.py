from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginViewTests(TestCase):
    def test_login_page_redirects_for_anonymous(self):
        response = self.client.get('/kiri-manage/login/')
        self.assertEqual(response.status_code, 200)
