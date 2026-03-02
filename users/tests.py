from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from users.models import UserIntegration
from users.encryption import encrypt_token, decrypt_token

User = get_user_model()


class UserSecurityTests(TestCase):
    """Test encryption and user constraints."""

    def test_encryption_roundtrip(self):
        token = "test_token_123456789"
        encrypted = encrypt_token(token)
        self.assertNotEqual(token, encrypted)
        self.assertEqual(token, decrypt_token(encrypted))

    def test_encryption_empty(self):
        self.assertEqual(encrypt_token(""), "")
        self.assertEqual(decrypt_token(""), "")

    def test_decrypt_corrupted_returns_empty(self):
        """Corrupted ciphertext returns empty string, not an exception."""
        result = decrypt_token("not-valid-fernet-data")
        self.assertEqual(result, "")

    def test_user_unique_platform_constraint(self):
        user = User.objects.create_user(username="testuser")
        UserIntegration.objects.create(
            user=user,
            platform=UserIntegration.Platform.GITHUB,
            platform_username="gh_user",
            access_token="abc"
        )
        with self.assertRaises(Exception):
            UserIntegration.objects.create(
                user=user,
                platform=UserIntegration.Platform.GITHUB,
                platform_username="gh_user2",
                access_token="def"
            )


class UserAdapterTests(TestCase):
    """Test adapter behavior."""

    def test_signup_closed(self):
        from users.adapter import KiriAccountAdapter
        adapter = KiriAccountAdapter()
        self.assertFalse(adapter.is_open_for_signup(None))

    def test_social_signup_closed(self):
        """Social signup is also blocked."""
        from users.adapter import KiriSocialAccountAdapter
        adapter = KiriSocialAccountAdapter()
        self.assertFalse(adapter.is_open_for_signup(None, None))

    def test_populate_user_github(self):
        """populate_user correctly maps GitHub fields."""
        from users.adapter import KiriSocialAccountAdapter
        adapter = KiriSocialAccountAdapter()

        mock_sociallogin = MagicMock()
        mock_sociallogin.account.provider = 'github'
        mock_sociallogin.account.extra_data = {
            'login': 'gh_testuser',
            'avatar_url': 'https://avatars.githubusercontent.com/test',
            'bio': 'Test bio',
        }

        mock_request = MagicMock()
        data = {'username': 'gh_testuser', 'email': 'test@example.com'}

        user = adapter.populate_user(mock_request, mock_sociallogin, data)

        self.assertEqual(user.username, 'gh_testuser')
        self.assertEqual(user.github_username, 'gh_testuser')
        self.assertEqual(user.github_avatar_url, 'https://avatars.githubusercontent.com/test')
        self.assertEqual(user.bio, 'Test bio')
        self.assertEqual(user.role, User.Role.CONTRIBUTOR)

    def test_populate_user_huggingface(self):
        """populate_user correctly maps HuggingFace fields."""
        from users.adapter import KiriSocialAccountAdapter
        adapter = KiriSocialAccountAdapter()

        mock_sociallogin = MagicMock()
        mock_sociallogin.account.provider = 'huggingface'
        mock_sociallogin.account.extra_data = {
            'preferred_username': 'hf_testuser',
            'picture': 'https://huggingface.co/avatars/test',
        }

        mock_request = MagicMock()
        data = {'username': 'hf_testuser'}

        user = adapter.populate_user(mock_request, mock_sociallogin, data)

        self.assertEqual(user.username, 'hf_testuser')
        self.assertEqual(user.huggingface_avatar_url, 'https://huggingface.co/avatars/test')
        self.assertEqual(user.role, User.Role.CONTRIBUTOR)

    def test_role_assignment(self):
        self.assertEqual(User.Role.CONTRIBUTOR, 'contributor')

    def test_pre_social_login_syncs_integration(self):
        """pre_social_login syncs integration for existing users."""
        from users.adapter import KiriSocialAccountAdapter
        adapter = KiriSocialAccountAdapter()

        user = User.objects.create_user(username='existing_user')

        mock_sociallogin = MagicMock()
        mock_sociallogin.is_existing = True
        mock_sociallogin.user = user
        mock_sociallogin.account.provider = 'github'
        mock_sociallogin.account.extra_data = {
            'login': 'existing_user',
            'avatar_url': '',
            'bio': '',
        }

        mock_request = MagicMock()

        with patch.object(adapter, '_update_user_from_social') as mock_update, \
             patch.object(adapter, '_create_or_update_integration') as mock_integration:
            adapter.pre_social_login(mock_request, mock_sociallogin)
            mock_update.assert_called_once_with(user, mock_sociallogin)
            mock_integration.assert_called_once_with(user, mock_sociallogin)


class LoginViewTests(TestCase):
    """Test login page behavior."""

    def test_login_page_loads(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Login')

    def test_login_uses_username(self):
        """Login page uses username field, not email."""
        response = self.client.get('/accounts/login/')
        self.assertContains(response, 'name="login"')
        self.assertContains(response, 'Username')
        self.assertNotContains(response, 'type="email"')

    def test_no_signup_link(self):
        """Login page does not link to signup."""
        response = self.client.get('/accounts/login/')
        self.assertNotContains(response, 'account_signup')
        self.assertNotContains(response, 'Initialize Profile')

    def test_no_password_reset_link(self):
        """Login page does not link to password reset."""
        response = self.client.get('/accounts/login/')
        self.assertNotContains(response, 'account_reset_password')
