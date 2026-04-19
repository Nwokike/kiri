from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Project
import os
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.utils.text import slugify

User = get_user_model()

class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password')
        self.project = Project.objects.create(
            name='Test Project',
            description='A test description',
            github_repo_url='https://github.com/tester/test',
            status='active'
        )

    def test_slug_generation_and_uniqueness(self):
        self.assertEqual(self.project.slug, 'test-project')
        project2 = Project.objects.create(
            name='Test Project',
            description='Another description',
            github_repo_url='https://github.com/tester/test2'
        )
        self.assertEqual(project2.slug, 'test-project-1')

    def test_preview_image_url(self):
        self.assertEqual(self.project.preview_image_url, 'https://opengraph.githubassets.com/1/tester/test')
        self.project.custom_image_url = 'https://example.com/image.png'
        self.project.save()
        self.assertEqual(self.project.preview_image_url, 'https://example.com/image.png')

class ProjectViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password', is_staff=True)
        self.project = Project.objects.create(
            name='Project 1',
            description='Active',
            status='active'
        )

    def test_list_view(self):
        url = reverse('projects:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Project 1')

    def test_detail_view(self):
        url = reverse('projects:detail', kwargs={'slug': self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_submit_view_requires_staff(self):
        url = reverse('projects:create_manual')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_fb_post_view_requires_staff(self):
        url = reverse('projects:fb_post', kwargs={'slug': self.project.slug})
        # Unauthenticated
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Non-staff
        user2 = User.objects.create_user(username='tester2', password='password', is_staff=False)
        self.client.force_login(user2)
        response = self.client.post(url)
        # Mixin returns 403 for authenticated non-staff
        self.assertIn(response.status_code, [302, 403])
        
        # Staff
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(response.url.endswith(reverse('projects:detail', kwargs={'slug': self.project.slug})))

class ProjectAutomationTests(TransactionTestCase):
    def test_auto_post_triggered_on_creation(self):
        with patch('kiri_project.tasks.post_to_facebook') as mock_fb:
            Project.objects.create(
                name='New Auto Project',
                description='Testing auto post',
                status='active'
            )
            self.assertTrue(mock_fb.called)
            self.assertEqual(mock_fb.call_args[0][0], 'project')

    def test_auto_post_not_triggered_on_update(self):
        project = Project.objects.create(name='Existing', description='desc')
        with patch('kiri_project.tasks.post_to_facebook') as mock_fb:
            project.save()
            self.assertFalse(mock_fb.called)

class ProjectTaskTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project',
            description='A test project description',
            github_repo_url='https://github.com/kiri-labs/test-project'
        )

    @patch('requests.post')
    def test_post_project_to_facebook(self, mock_post):
        from kiri_project.tasks import post_to_facebook
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {
            'META_PAGE_ID': '123',
            'LONG_META_PAGE_TOKEN': 'abc'
        }), self.settings(SITE_URL='https://kiri.ng'):
            # In Huey 3.x, use .underlying to call the function directly
            func = getattr(post_to_facebook, 'underlying', post_to_facebook)
            func('project', self.project.id)
            self.assertTrue(mock_post.called)
            args, kwargs = mock_post.call_args
            message = kwargs['data']['message']
            self.assertIn('https://kiri.ng/projects/test-project/', message)
            self.assertEqual(kwargs['headers']['Authorization'], 'Bearer abc')
