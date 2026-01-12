from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from users.models import orcid_validator

User = get_user_model()

class CustomUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password123',
            role=User.Role.RESEARCHER,
            is_profile_public=True
        )
        self.private_user = User.objects.create_user(
            username='privateuser',
            password='password123',
            is_profile_public=False
        )

    def test_create_user_fields(self):
        """Test user creation and field defaults."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('password123'))
        self.assertEqual(self.user.role, 'researcher')
        self.assertTrue(self.user.is_profile_public)

    def test_orcid_validation(self):
        """Test ORCID validator."""
        valid_orcid = "0000-0001-2345-6789"
        invalid_orcid = "123-abc"
        
        # Should not raise exception
        orcid_validator(valid_orcid)
        
        with self.assertRaises(ValidationError):
            orcid_validator(invalid_orcid)

    def test_public_profile_view(self):
        """Test viewing a public profile."""
        response = self.client.get(reverse('users:profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Researcher')

    def test_private_profile_view_anonymous(self):
        """Test viewing a private profile as anonymous user."""
        response = self.client.get(reverse('users:profile', kwargs={'username': 'privateuser'}))
        # Logic in view: if not owner and not staff -> 404 (filtered out of queryset)
        self.assertEqual(response.status_code, 404)

    def test_private_profile_view_owner(self):
        """Test viewing own private profile."""
        self.client.login(username='privateuser', password='password123')
        response = self.client.get(reverse('users:profile', kwargs={'username': 'privateuser'}))
        self.assertEqual(response.status_code, 200)

    def test_private_profile_view_other(self):
        """Test viewing other's private profile."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('users:profile', kwargs={'username': 'privateuser'}))
        self.assertEqual(response.status_code, 404)
