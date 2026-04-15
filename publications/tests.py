from django.test import TestCase
from django.urls import reverse
from .models import Publication
from .utils import process_markdown
from django.utils.text import slugify

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
        self.assertTemplateUsed(response, 'publications/publication_list.html')

    def test_detail_view(self):
        response = self.client.get(reverse('publications:detail', args=[self.pub.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Title')
        self.assertContains(response, '<p>Hello World</p>')
        self.assertTemplateUsed(response, 'publications/publication_detail.html')

class MarkdownUtilsTest(TestCase):
    def test_image_link_rewrite(self):
        raw = "![alt](docs/img.png)"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("https://raw.githubusercontent.com/owner/repo/main/docs/img.png", html)

    def test_image_link_rewrite_root(self):
        # test image link at root without docs/
        raw = "![alt](image.png)"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("https://raw.githubusercontent.com/owner/repo/main/image.png", html)

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
        # ensure string is not broken if empty
        html = process_markdown("owner", "repo", "")
        self.assertEqual(html, "")

    def test_complex_code_blocks(self):
        raw = "```python\nprint('hello')\n```"
        html = process_markdown("owner", "repo", "main", raw)
        self.assertIn("codehilite", html)
        self.assertNotIn("```", html)
