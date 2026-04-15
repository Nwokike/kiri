from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from .models import Publication

@method_decorator(login_not_required, name='dispatch')
class PublicationListView(ListView):
    model = Publication
    template_name = 'publications/publication_list.html'
    context_object_name = 'publications'
    paginate_by = 12

@method_decorator(login_not_required, name='dispatch')
class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'publications/publication_detail.html'
    context_object_name = 'publication'
