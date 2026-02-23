from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
        )

    def test_create_user_fields(self):
        """Test user creation and field defaults."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('password123'))

    def test_avatar_url_priority(self):
        """Test avatar_url property returns GitHub > HuggingFace > None."""
        self.assertIsNone(self.user.avatar_url)
        
        self.user.huggingface_avatar_url = 'https://hf.example.com/avatar.png'
        self.assertEqual(self.user.avatar_url, 'https://hf.example.com/avatar.png')
        
        self.user.github_avatar_url = 'https://github.example.com/avatar.png'
        self.assertEqual(self.user.avatar_url, 'https://github.example.com/avatar.png')
