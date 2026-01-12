from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from core.models import Comment
from projects.models import Project

User = get_user_model()

class CoreTests(TestCase):
    """Tests for Core app views and pages."""
    
    def test_home_page(self):
        """Test home page renders correctly."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_universal_translator_demo(self):
        """Test universal translator demo page."""
        response = self.client.get(reverse('core:universal_translator'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'demos/universal_translator.html')
        
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

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
        self.assertNotEqual(response.status_code, 200) # Redirects to login

    def test_comment_xss_sanitization(self):
        """Test that HTML tags are sanitized."""
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        script_content = '<script>alert("XSS")</script>Hello<b>Bold</b>'
        response = self.client.post(url, {'content': script_content})
        
        # Verify sanitization
        comment = Comment.objects.get(author=self.user)
        self.assertNotIn('<script>', comment.content)
        # With strip=True, tags are removed, not escaped.
        self.assertIn('alert("XSS")', comment.content) # Content remains
        self.assertIn('<b>Bold</b>', comment.content)  # Allowed tags remain
        # Standard bleach: strips tags.
        
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
        self.assertEqual(response.status_code, 400) # We changed Forbidden to 400 Bad Request with error template
        self.assertTemplateUsed(response, 'core/partials/comment_form_errors.html')
