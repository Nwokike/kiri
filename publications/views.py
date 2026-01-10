from django.views.generic import ListView, DetailView
from .models import Publication

class PublicationListView(ListView):
    model = Publication
    template_name = 'publications/publication_list.html'
    context_object_name = 'publications'
    paginate_by = 9
    
    def get_queryset(self):
        return Publication.objects.filter(is_published=True)

class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'publications/publication_detail.html'
    context_object_name = 'publication'
    
    def get_queryset(self):
        return Publication.objects.filter(is_published=True)
