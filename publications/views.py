from django.views.generic import ListView, DetailView
from django.contrib.contenttypes.models import ContentType
from .models import Publication
from core.models import Comment
from core.forms import CommentForm

class PublicationListView(ListView):
    model = Publication
    template_name = 'publications/publication_list.html'
    context_object_name = 'publications'
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Publication.objects.filter(is_published=True)

class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'publications/publication_detail.html'
    context_object_name = 'publication'
    def get_queryset(self):
        return Publication.objects.filter(is_published=True)
