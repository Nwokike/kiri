from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Publication

User = get_user_model()

class PublicationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='password')
        self.pub = Publication.objects.create(
            title='Research Paper',
            author=self.user,
            abstract='Abstract here.',
            content='# Markdown content',
            is_published=True,
            version=1
        )

    def test_publication_list(self):
        response = self.client.get(reverse('publications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Research Paper')

    def test_publication_detail(self):
        response = self.client.get(reverse('publications:detail', kwargs={'slug': self.pub.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'v1')
