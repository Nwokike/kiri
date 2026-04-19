from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class CoreTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_page(self):
        response = self.client.get(reverse('core:privacy'))
        self.assertEqual(response.status_code, 200)

    def test_terms_page(self):
        response = self.client.get(reverse('core:terms'))
        self.assertEqual(response.status_code, 200)

    def test_404_page(self):
        response = self.client.get('/nonexistent-page-xyz/')
        self.assertEqual(response.status_code, 404)

class NativeTaskTests(TestCase):
    def test_task_registration(self):
        from kiri_project.tasks import sync_github_stats, cleanup_tmp_files, prune_cache_table
        from huey.api import TaskWrapper
        self.assertIsInstance(sync_github_stats, TaskWrapper)
        self.assertIsInstance(cleanup_tmp_files, TaskWrapper)
        self.assertIsInstance(prune_cache_table, TaskWrapper)
