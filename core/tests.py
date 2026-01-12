from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from core.models import Comment
from projects.models import Project

User = get_user_model()

class CoreTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_universal_translator_demo(self):
        response = self.client.get(reverse('core:universal_translator'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'demos/universal_translator.html')

class GenericCommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='password')
        self.project_content_type = ContentType.objects.get_for_model(Project)
        self.project = Project.objects.create(name='Test Proj', submitted_by=self.user)

    def test_add_comment(self):
        self.client.login(username='commenter', password='password')
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': 'Nice project!'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(content='Nice project!').exists())

    def test_add_comment_unauthenticated(self):
        url = reverse('core:add_comment', kwargs={
            'content_type_id': self.project_content_type.id,
            'object_id': self.project.id
        })
        response = self.client.post(url, {'content': 'Anon comment'})
        self.assertNotEqual(response.status_code, 200) # Should verify login required logic
