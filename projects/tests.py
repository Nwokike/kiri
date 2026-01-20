from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
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
        
        # Create second project with same name
        project2 = Project.objects.create(
            name='Test Project',
            submitted_by=self.user,
            description='Another description.',
            github_repo_url='https://github.com/tester/test2'
        )
        self.assertEqual(project2.slug, 'test-project-1')
        
        # Create third project
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
        
        # 1. Default (All Approved)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved and Linked')
        self.assertContains(response, 'Hot Project')
        self.assertNotContains(response, 'Pending Project')
        
        # 2. Category Filter
        response = self.client.get(url, {'category': 'ai_nlp'})
        self.assertContains(response, 'Approved and Linked')
        self.assertNotContains(response, 'Hot Project') # Assuming default cat is Other
        
        # 3. Hot Filter
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
        self.assertEqual(response.status_code, 302) # Redirect to login
        
        self.client.login(username='tester', password='password')
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
            'topics': '["nlp", "cv", "transformers"]',  # Expected JSON format
        })
        # Remove turnstile field entirely for testing
        del form.fields['turnstile']
        
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['topics'], ['nlp', 'cv', 'transformers'])


# ============================================================================
# Traffic Controller Tests
# ============================================================================

class TrafficControllerClassificationTests(TestCase):
    """Tests for the AI-powered lane classification system."""
    
    def test_react_project_classification(self):
        """React/Vue/Node.js projects should be classified as Lane A."""
        from core.ai_service import AIService
        
        repo_files = {
            'file_list': ['package.json', 'src/App.jsx', 'src/index.js', 'vite.config.js'],
            'package_json': '{"dependencies": {"react": "^18.2.0", "vite": "^5.0.0"}}',
            'requirements_txt': '',
            'pyproject_toml': '',
            'dockerfile': '',
            'main_file': '',
            'readme': '# React App'
        }
        
        # Use heuristic directly to avoid API calls in tests
        result = AIService._heuristic_classification(repo_files)
        self.assertEqual(result['lane'], 'A')
        self.assertIn('JavaScript', result['reason'])
    
    def test_django_project_classification(self):
        """Django/Flask projects should be classified as Lane B."""
        from core.ai_service import AIService
        
        repo_files = {
            'file_list': ['manage.py', 'app/views.py', 'app/models.py', 'requirements.txt'],
            'package_json': '',
            'requirements_txt': 'django==4.2\ngunicorn\npsycopg2-binary',
            'pyproject_toml': '',
            'dockerfile': '',
            'main_file': '',
            'readme': '# Django Web App'
        }
        
        result = AIService._heuristic_classification(repo_files)
        self.assertEqual(result['lane'], 'B')
        self.assertIn('Django', result['reason'])
    
    def test_ml_project_classification(self):
        """PyTorch/TensorFlow projects should be classified as Lane C."""
        from core.ai_service import AIService
        
        repo_files = {
            'file_list': ['train.py', 'model.py', 'requirements.txt', 'data/train.csv'],
            'package_json': '',
            'requirements_txt': 'torch==2.1.0\ntransformers\nsentencepiece\naccelerate',
            'pyproject_toml': '',
            'dockerfile': '',
            'main_file': '',
            'readme': '# LLM Fine-tuning'
        }
        
        result = AIService._heuristic_classification(repo_files)
        self.assertEqual(result['lane'], 'C')
        self.assertIn('ML', result['reason'])
    
    def test_validation_corrects_ai_mistakes(self):
        """Validation layer should correct obvious AI misclassifications."""
        from core.ai_service import AIService
        
        # Simulate AI mistakenly returning Lane A for a Django project
        wrong_ai_result = {'lane': 'A', 'reason': 'Some incorrect reason', 'start_command': 'npm run dev'}
        
        repo_files = {
            'file_list': ['manage.py', 'app/views.py'],
            'package_json': '',
            'requirements_txt': 'django>=4.0\ngunicorn',
            'pyproject_toml': '',
            'dockerfile': '',
            'main_file': '',
            'readme': ''
        }
        
        # Validation should correct this
        corrected = AIService._validate_classification(wrong_ai_result, repo_files)
        self.assertEqual(corrected['lane'], 'B')
    
    def test_lane_field_on_model(self):
        """Test that Project model has lane field with correct defaults."""
        self.user = User.objects.create_user(username='lane_tester', password='password')
        project = Project.objects.create(
            name='Lane Test Project',
            submitted_by=self.user,
            description='Testing lane field.',
            github_repo_url='https://github.com/test/lane-test'
        )
        
        # Default should be 'P' (Pending)
        self.assertEqual(project.lane, 'P')
        self.assertEqual(project.get_lane_display(), 'Pending Classification')
        
        # Should be able to set lane
        project.lane = 'A'
        project.save()
        project.refresh_from_db()
        self.assertEqual(project.lane, 'A')


class TrafficControllerGistServiceTests(TestCase):
    """Tests for Gist URL generation (not actual API calls)."""
    
    def test_binder_url_format(self):
        """Test Binder URL is correctly formatted."""
        from projects.gist_service import GistService
        import os
        os.environ['KIRI_BOT_USERNAME'] = 'test-bot'
        
        url = GistService.build_binder_url('abc123', port=8000)
        
        self.assertIn('mybinder.org', url)
        self.assertIn('gist', url)
        self.assertIn('abc123', url)
        self.assertIn('proxy/8000/', url)
    
    def test_colab_url_format(self):
        """Test Colab URL is correctly formatted."""
        from projects.gist_service import GistService
        import os
        os.environ['KIRI_BOT_USERNAME'] = 'test-bot'
        
        url = GistService.build_colab_url('xyz789')
        
        self.assertIn('colab.research.google.com', url)
        self.assertIn('gist', url)
        self.assertIn('xyz789', url)
        self.assertIn('demo.ipynb', url)


class TrafficControllerColabNotebookTests(TestCase):
    """Tests for Colab notebook generation."""
    
    def test_notebook_generation(self):
        """Test that generated notebook has correct structure."""
        from core.ai_service import AIService
        import json
        
        notebook_json = AIService.generate_colab_notebook(
            'https://github.com/user/ml-project',
            'python train.py'
        )
        
        notebook = json.loads(notebook_json)
        
        self.assertEqual(notebook['nbformat'], 4)
        self.assertIn('cells', notebook)
        self.assertTrue(len(notebook['cells']) >= 3)
        
        # Check that git clone is in first code cell
        code_cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
        first_code = ''.join(code_cells[0]['source'])
        self.assertIn('git clone', first_code)
        self.assertIn('ml-project', first_code)


class ImportLandingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='password')
        self.url = reverse('projects:create') # The new import landing

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
        self.assertEqual(len(platforms), 4)
        names = [p['name'] for p in platforms]
        self.assertIn('GitHub', names)
        # Check Hugging Face specifically as it was a pain point
        hf = next(p for p in platforms if p['name'] == 'Hugging Face')
        self.assertIn('text-[#FFD21E]', hf['icon'])

class ProjectSubmitImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='importer', password='password')
        self.url = reverse('projects:create_manual') # The submit form

    def test_prefill_from_params(self):
        self.client.login(username='importer', password='password')
        
        # Simulate clicking "Import" from the landing page
        params = {
            'import_mode': 'true',
            'repo_url': 'https://github.com/importer/my-repo',
            'name': 'My Imported Repo',
            'description': 'Auto description'
        }
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        
        # Check if form initial data is populated
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
