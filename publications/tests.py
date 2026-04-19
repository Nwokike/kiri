from django.test import TestCase
from django.urls import reverse
from .models import Publication
from .utils import process_markdown
from django.utils.text import slugify
import os
from unittest.mock import patch, MagicMock
from django.conf import settings

class PublicationModelTest(TestCase):
    def setUp(self):
        self.pub = Publication.objects.create(
            repo_name='test-repo',
            title='Test Title',
            slug='test-repo',
            description='Test Description',
            html_content='<p>Hello World</p>',
            github_url='https://github.com/Kiri-Research-Labs/test-repo',
            topics='test,django'
        )

    def test_publication_creation(self):
        self.assertEqual(self.pub.title, 'Test Title')
        self.assertEqual(self.pub.slug, 'test-repo')
        self.assertEqual(self.pub.get_absolute_url(), '/publications/test-repo/')

class PublicationViewsTest(TestCase):
    def setUp(self):
        self.pub = Publication.objects.create(
            repo_name='test-repo',
            title='Test Title',
            slug='test-repo',
            description='Test Description',
            html_content='<p>Hello World</p>',
            github_url='https://github.com/Kiri-Research-Labs/test-repo',
            topics='test,django'
        )

    def test_list_view(self):
        response = self.client.get(reverse('publications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Title')

    def test_detail_view(self):
        response = self.client.get(reverse('publications:detail', kwargs={'slug': self.pub.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Title')
        self.assertContains(response, '<p>Hello World</p>')
        self.assertTemplateUsed(response, 'publications/publication_detail.html')

    def test_fb_post_view_requires_staff(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        staff_user = User.objects.create_user(username='staff', password='password', is_staff=True)
        
        url = reverse('publications:fb_post', kwargs={'slug': self.pub.slug})
        
        # Unauthenticated
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Staff
        self.client.force_login(staff_user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('publications:detail', kwargs={'slug': self.pub.slug})))


class MarkdownUtilsTest(TestCase):
    def test_image_link_rewrite(self):
        raw = "![alt](docs/img.png)"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("https://raw.githubusercontent.com/owner/repo/main/docs/img.png", html)

    def test_document_link_rewrite(self):
        raw = "[setup](docs/setup.md)"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("https://github.com/owner/repo/blob/main/docs/setup.md", html)

    def test_absolute_link_not_rewritten(self):
        raw = "[google](https://google.com)"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("href=\"https://google.com\"", html)
        self.assertNotIn("blob/main", html)

    def test_empty_content(self):
        html = process_markdown("owner", "repo", "main", "")
        self.assertEqual(html, "")

    def test_complex_code_blocks(self):
        raw = "```python\nprint('hello')\n```"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("codehilite", html)
        self.assertNotIn("```", html)

class PublicationTaskTests(TestCase):
    def setUp(self):
        self.pub = Publication.objects.create(
            repo_name='test-pub',
            title='Test Publication',
            slug='test-pub',
            description='A test publication description',
            github_url='https://github.com/kiri-labs/test-pub'
        )

    @patch('requests.post')
    def test_post_publication_to_facebook(self, mock_post):
        from kiri_project.tasks import post_to_facebook
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {
            'META_PAGE_ID': '123',
            'LONG_META_PAGE_TOKEN': 'abc'
        }), self.settings(SITE_URL='https://kiri.ng'):
            # Use .underlying to call the function directly
            func = getattr(post_to_facebook, 'underlying', post_to_facebook)
            func('publication', self.pub.id)
            self.assertTrue(mock_post.called)
            args, kwargs = mock_post.call_args
            message = kwargs['data']['message']
            self.assertIn('https://kiri.ng/publications/test-pub/', message)
            self.assertEqual(kwargs['headers']['Authorization'], 'Bearer abc')
