from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from django.contrib.contenttypes.models import ContentType
from projects.models import Project

User = get_user_model()

class CoreTests(TestCase):
    """Tests for Core app views and pages."""
    
    def test_home_page(self):
        """Test home page renders correctly."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_global_login_required(self):
        """Test that LoginRequiredMiddleware is active."""
        url = reverse('projects:create_manual')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_public_view_exemptions(self):
        """Test that public views are exempted from login."""
        url = reverse('core:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_csp_middleware_active(self):
        """Test that ContentSecurityPolicyMiddleware is sending headers."""
        response = self.client.get(reverse('core:home'))
        self.assertIn('Content-Security-Policy', response.headers)

class NativeTaskTests(TestCase):
    """Tests for the native Django 6.0 task framework."""

    def test_task_registration(self):
        """Test that key background tasks are registered."""
        from kiri_project.tasks import (
            update_project_hot_status, backup_db_to_r2,
            sync_github_stats, dummy_task,
        )
        from django.tasks import Task

        self.assertIsInstance(update_project_hot_status, Task)
        self.assertIsInstance(backup_db_to_r2, Task)
        self.assertIsInstance(sync_github_stats, Task)
        self.assertIsInstance(dummy_task, Task)

    def test_task_enqueue(self):
        """Test that we can enqueue a task without errors."""
        from kiri_project.tasks import dummy_task
        result = dummy_task.enqueue(1, 2)
        self.assertIsNotNone(result)


@override_settings(TESTING=True)
class GenericCommentTests(TestCase):
    """Placeholder for generic tests if needed in future."""
    pass
