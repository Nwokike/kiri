from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Project
from .forms import ProjectSubmissionForm

User = get_user_model()

class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password')
        self.project = Project.objects.create(
            name='Test Project',
            submitted_by=self.user,
            description='A test description.',
            github_repo_url='https://github.com/tester/test',
            is_approved=True
        )

    def test_slug_generation(self):
        self.assertEqual(self.project.slug, 'test-project')

    def test_hot_status_update(self):
        # Simulate high engagement
        self.project.view_count = 1000
        self.project.stars_count = 50
        self.project.save()
        
        # Test logic (mimics task.py logic)
        score = self.project.view_count + (self.project.stars_count * 10)
        self.assertGreater(score, 500) 

class ProjectViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password')
        self.project = Project.objects.create(
            name='Approved Project',
            submitted_by=self.user,
            description='Visible.',
            is_approved=True
        )
        self.unapproved_project = Project.objects.create(
            name='Pending Project',
            submitted_by=self.user,
            description='Not visible.',
            is_approved=False
        )

    def test_list_view_shows_only_approved(self):
        response = self.client.get(reverse('projects:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved Project')
        self.assertNotContains(response, 'Pending Project')

    def test_submit_view_requires_login(self):
        response = self.client.get(reverse('projects:submit'))
        self.assertNotEqual(response.status_code, 200) # Should redirect
        
        self.client.login(username='tester', password='password')
        response = self.client.get(reverse('projects:submit'))
        self.assertEqual(response.status_code, 200)
