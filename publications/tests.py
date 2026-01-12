from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Publication

User = get_user_model()

class PublicationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.pub = Publication.objects.create(
            title="Test Publication",
            abstract="Abstract here",
            content="# Heading\nContent",
            author=self.user,
            is_published=True
        )

    def test_slug_generation(self):
        self.assertEqual(self.pub.slug, 'test-publication')
        
    def test_slug_collision(self):
        pub2 = Publication.objects.create(
            title="Test Publication",
            abstract="Abstract 2",
            content="Content 2",
            author=self.user,
            is_published=True
        )
        self.assertEqual(pub2.slug, 'test-publication-1')

    def test_version_increment(self):
        self.pub.content = "New content"
        self.pub.save()
        self.assertEqual(self.pub.version, 2)
        
    def test_view_count_default(self):
        self.assertEqual(self.pub.view_count, 0)


class PublicationViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        self.pub = Publication.objects.create(
            title="AI Research",
            abstract="Deep learning",
            content="Markdown content",
            author=self.user,
            is_published=True
        )
        self.url = reverse('publications:detail', kwargs={'slug': self.pub.slug})

    def test_list_view(self):
        response = self.client.get(reverse('publications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Research")

    def test_list_search(self):
        response = self.client.get(reverse('publications:list') + '?q=Deep')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Research")
        
        response = self.client.get(reverse('publications:list') + '?q=Quantum')
        self.assertNotContains(response, "AI Research")

    def test_detail_view_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('comments', response.context)
        self.assertIn('comment_form', response.context)

    def test_view_count_increment(self):
        initial_views = self.pub.view_count
        self.client.get(self.url)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.view_count, initial_views + 1)

    def test_unpublished_access(self):
        self.pub.is_published = False
        self.pub.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(response.status_code, 404)
