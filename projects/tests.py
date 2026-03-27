from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Project

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
        self.archived_project = Project.objects.create(
            name='Project 2',
            description='Archived',
            status='archived'
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
        
        self.client.login(username='tester', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
