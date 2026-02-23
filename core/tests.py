from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from django.contrib.contenttypes.models import ContentType
from core.models import Comment
from projects.models import Project
from django.tasks import task, task_backends

@task
def dummy_task(x, y):
    return x + y

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

class AIServiceFallbackTests(TestCase):
    """Tests for the multi-tier AI fallback rotation logic."""

    @patch('requests.post')
    def test_model_rotation_on_429(self, mock_post):
        """Test that AIService rotates to the next model on 429."""
        from core.ai_service import AIService
        
        mock_post.side_effect = [
            type('Response', (), {'status_code': 429}),
            type('Response', (), {'status_code': 429}),
            type('Response', (), {
                'status_code': 200,
                'json': lambda: {
                    'choices': [{'message': {'content': '{"status": "ok", "result": "test"}'}}]
                }
            })
        ]
        
        result = AIService.generate_json_sync("Test prompt")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['_ai_model'], AIService.AI_MODELS[2]['model'])
        self.assertEqual(mock_post.call_count, 3)

    @patch('requests.post')
    def test_fallback_to_gemini(self, mock_post):
        """Test that it falls back to Gemini if all Groq models fail."""
        from core.ai_service import AIService
        
        responses = [type('Response', (), {'status_code': 429}) for _ in range(8)]
        responses.append(type('Response', (), {
            'status_code': 200,
            'json': lambda: {
                'candidates': [{'content': {'parts': [{'text': '{"status": "ok", "result": "Gemini fallback"}'}]}}]
            }
        }))
        
        mock_post.side_effect = responses
        
        result = AIService.generate_json_sync("Test prompt")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['_ai_model'], AIService.AI_MODELS[8]['model'])

    @patch('requests.post')
    def test_absolute_last_resort(self, mock_post):
        """Test that it reaches the very last model if all others fail."""
        from core.ai_service import AIService
        
        responses = [type('Response', (), {'status_code': 429}) for _ in range(13)]
        responses.append(type('Response', (), {
            'status_code': 200,
            'json': lambda: {
                'choices': [{'message': {'content': '{"status": "ok", "result": "Last resort"}'}}]
            }
        }))
        
        mock_post.side_effect = responses
        
        result = AIService.generate_json_sync("Test prompt")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['_ai_model'], "llama-3.1-8b-instant")

class NativeTaskTests(TestCase):
    """Tests for the native Django 6.0 task framework."""

    def test_task_registration(self):
        """Test that key background tasks are registered."""
        from kiri_project.tasks import (
            update_project_hot_status, backup_db_to_r2, 
            sync_github_stats
        )
        from django.tasks import Task
        
        self.assertIsInstance(update_project_hot_status, Task)
        self.assertIsInstance(backup_db_to_r2, Task)
        self.assertIsInstance(sync_github_stats, Task)

    def test_task_enqueue(self):
        """Test that we can enqueue a task without errors."""
        result = dummy_task.enqueue(1, 2)
        self.assertIsNotNone(result)

@override_settings(TESTING=True)
class GenericCommentTests(TestCase):
    """Tests for the generic comment system."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='password')
        self.project_content_type = ContentType.objects.get_for_model(Project)
        self.project = Project.objects.create(name='Test Proj', submitted_by=self.user)

    def test_add_comment(self):
        """Test adding a valid comment."""
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': 'Nice project!'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(content='Nice project!').exists())

    def test_add_comment_unauthenticated(self):
        """Test unauthenticated comment submission."""
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': 'Anon comment'})
        self.assertNotEqual(response.status_code, 200)

    def test_comment_xss_sanitization(self):
        """Test that HTML tags are sanitized."""
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        script_content = '<script>alert("XSS")</script>Hello<b>Bold</b>'
        response = self.client.post(url, {'content': script_content})
        
        comment = Comment.objects.get(author=self.user)
        self.assertNotIn('<script>', comment.content)
        self.assertNotIn('alert("XSS")', comment.content) 
        self.assertIn('Hello', comment.content)
        self.assertIn('<b>Bold</b>', comment.content)
        
    def test_invalid_content_type(self):
        """Test commenting on non-existent content type."""
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': 9999,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': 'Fail'})
        self.assertEqual(response.status_code, 404)

    def test_empty_comment(self):
        """Test submission of empty comment."""
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': ''})
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'core/partials/comment_form_errors.html')
