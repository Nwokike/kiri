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
    paginate_by = 12
    
    def get_queryset(self):
        from django.db.models import Q
        
        qs = Publication.objects.filter(is_published=True).select_related('author')
        
        # Search functionality
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) | 
                Q(abstract__icontains=query) |
                Q(content__icontains=query)
            )
            
        return qs.order_by('-created_at')

class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'publications/publication_detail.html'
    context_object_name = 'publication'

    def get_queryset(self):
        return Publication.objects.filter(is_published=True).select_related('author').prefetch_related('contributors')

    def get_context_data(self, **kwargs):
        from django.contrib.contenttypes.models import ContentType
        from core.models import Comment
        from core.forms import CommentForm
        from django.db.models import Prefetch, F

        context = super().get_context_data(**kwargs)
        
        # Atomic View Count Increment
        Publication.objects.filter(pk=self.object.pk).update(view_count=F('view_count') + 1)
        self.object.refresh_from_db(fields=['view_count'])
        
        # Comments context
        content_type = ContentType.objects.get_for_model(Publication)
        from django.db.models import Prefetch
        
        comments = Comment.objects.filter(
            content_type=content_type,
            object_id=self.object.id,
            parent__isnull=True
        ).select_related('author').prefetch_related(
            Prefetch('replies', queryset=Comment.objects.select_related('author'))
        )
        
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        return context
