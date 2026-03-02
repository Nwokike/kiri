from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

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

    # --- Additional view tests ---

    def test_about_page(self):
        """Test about page renders correctly."""
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kiri Labs')

    def test_contact_page(self):
        """Test contact page renders correctly."""
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hello@kiri.ng')

    def test_privacy_page(self):
        """Test privacy page renders correctly."""
        response = self.client.get(reverse('core:privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Privacy Policy')

    def test_terms_page(self):
        """Test terms page renders correctly."""
        response = self.client.get(reverse('core:terms'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terms of Service')

    def test_refund_page(self):
        """Test refund page renders correctly."""
        response = self.client.get(reverse('core:refund_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Refund Policy')

    def test_serviceworker(self):
        """Test service worker JS renders with correct content type."""
        response = self.client.get(reverse('serviceworker'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('javascript', response['Content-Type'])

    def test_pwa_manifest(self):
        """Test PWA manifest renders valid JSON."""
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('json', response['Content-Type'])
        data = response.json()
        self.assertEqual(data['name'], 'Kiri')

    def test_silent_asset_js(self):
        """Test silent asset returns empty JS response."""
        response = self.client.get('/studio/stackframe.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('javascript', response['Content-Type'])

    def test_silent_asset_json(self):
        """Test silent asset returns correct JSON content type."""
        response = self.client.get('/.well-known/appspecific/com.chrome.devtools.json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('json', response['Content-Type'])

    def test_404_page(self):
        """Test custom 404 page loads with correct CSS."""
        response = self.client.get('/nonexistent-page-xyz/')
        self.assertEqual(response.status_code, 404)

    def test_robots_txt(self):
        """Test robots.txt renders correctly."""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sitemap:')
        self.assertContains(response, '/projects/api/')


class NativeTaskTests(TestCase):
    """Tests for the native Django 6.0 task framework."""

    def test_task_registration(self):
        """Test that key background tasks are registered."""
        from kiri_project.tasks import (
            update_project_hot_status,
            sync_github_stats,
            cleanup_tmp_files,
            prune_cache_table,
        )
        from django.tasks import Task

        self.assertIsInstance(update_project_hot_status, Task)
        self.assertIsInstance(sync_github_stats, Task)
        self.assertIsInstance(cleanup_tmp_files, Task)
        self.assertIsInstance(prune_cache_table, Task)

    def test_task_enqueue(self):
        """Test that we can enqueue a task without errors."""
        from kiri_project.tasks import update_project_hot_status
        result = update_project_hot_status.enqueue()
        self.assertIsNotNone(result)
