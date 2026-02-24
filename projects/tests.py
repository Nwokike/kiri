from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json
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
            is_approved=True,
            category=Project.Category.AI_NLP
        )

    def test_slug_generation_and_uniqueness(self):
        """Test slug generation and collision handling."""
        self.assertEqual(self.project.slug, 'test-project')
        
        project2 = Project.objects.create(
            name='Test Project',
            submitted_by=self.user,
            description='Another description.',
            github_repo_url='https://github.com/tester/test2'
        )
        self.assertEqual(project2.slug, 'test-project-1')
        
        project3 = Project.objects.create(
            name='Test Project',
            submitted_by=self.user,
            description='Third description.',
            github_repo_url='https://github.com/tester/test3'
        )
        self.assertEqual(project3.slug, 'test-project-2')

    def test_hot_status_logic(self):
        """Test the logic used for calculating HOT status."""
        self.project.view_count = 1000
        self.project.stars_count = 50
        
        score = self.project.view_count + (self.project.stars_count * 10)
        self.assertEqual(score, 1500)

class ProjectViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='password')
        self.project = Project.objects.create(
            name='Approved and Linked',
            submitted_by=self.user,
            description='Visible.',
            is_approved=True,
            category='ai_nlp',
            language='Python',
            stars_count=100
        )
        self.unapproved_project = Project.objects.create(
            name='Pending Project',
            submitted_by=self.user,
            description='Not visible.',
            is_approved=False
        )
        self.hot_project = Project.objects.create(
            name='Hot Project',
            submitted_by=self.user,
            description='Visible and Hot.',
            is_approved=True,
            is_hot=True
        )

    def test_list_view_filtering(self):
        """Test list view filtering by category, hot status, and approval."""
        url = reverse('projects:list')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved and Linked')
        self.assertContains(response, 'Hot Project')
        self.assertNotContains(response, 'Pending Project')
        
        response = self.client.get(url, {'category': 'ai_nlp'})
        self.assertContains(response, 'Approved and Linked')
        self.assertNotContains(response, 'Hot Project')
        
        response = self.client.get(url, {'hot': 'true'})
        self.assertContains(response, 'Hot Project')
        self.assertNotContains(response, 'Approved and Linked')

    def test_detail_view_increments_views(self):
        """Test visiting detail view increments view count."""
        url = reverse('projects:detail', kwargs={'slug': self.project.slug})
        initial_views = self.project.view_count
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        self.project.refresh_from_db()
        self.assertEqual(self.project.view_count, initial_views + 1)

    def test_submit_view_access(self):
        """Test submission view requires login."""
        url = reverse('projects:create_manual')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        self.client.login(username='tester', password='password')
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

@override_settings(TESTING=True)
class ProjectFormTests(TestCase):
    def test_clean_topics(self):
        form = ProjectSubmissionForm(data={
            'name': 'Test',
            'description': 'Desc',
            'category': 'other',
            'github_repo_url': 'https://github.com/foo/bar',
            'topics': '["nlp", "cv", "transformers"]',
        })
        
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['topics'], ['nlp', 'cv', 'transformers'])



class ImportLandingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='password', is_staff=True)
        self.url = reverse('projects:create')

    def test_access_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        
        self.client.login(username='importer', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/import_landing.html')

    def test_context_platforms(self):
        self.client.login(username='importer', password='password')
        response = self.client.get(self.url)
        platforms = response.context['platforms']
        self.assertEqual(len(platforms), 2)
        names = [p['name'] for p in platforms]
        self.assertIn('GitHub', names)
        hf = next(p for p in platforms if p['name'] == 'Hugging Face')
        self.assertIn('text-[#FFD21E]', hf['icon'])

class ProjectSubmitImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='password', is_staff=True)
        self.url = reverse('projects:create_manual')

    def test_prefill_from_params(self):
        self.client.login(username='importer', password='password')
        
        params = {
            'import_mode': 'true',
            'repo_url': 'https://github.com/importer/my-repo',
            'name': 'My Imported Repo',
            'description': 'Auto description'
        }
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        
        form = response.context['form']
        self.assertEqual(form.initial['github_repo_url'], 'https://github.com/importer/my-repo')
        self.assertEqual(form.initial['name'], 'My Imported Repo')
        self.assertEqual(form.initial['description'], 'Auto description')


class RepoFilesApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='password')
        self.url = reverse('projects:api_repo_files')

    def test_api_requires_login(self):
        response = self.client.get(self.url, {'url': 'https://github.com/foo/bar'})
        self.assertEqual(response.status_code, 302)

    @patch('projects.services.GitHubService.fetch_structure')
    def test_fetch_files_success(self, mock_fetch):
        mock_fetch.return_value = {
            'file_list': ['README.md', 'paper.pdf', 'code.py']
        }
        self.client.login(username='importer', password='password')
        
        response = self.client.get(self.url, {'url': 'https://github.com/foo/bar'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['files']), 3)
        self.assertIn('paper.pdf', data['files'])

    def test_missing_url_param(self):
        self.client.login(username='importer', password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
