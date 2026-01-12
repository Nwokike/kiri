from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from .models import Project
from .forms import ProjectSubmissionForm
from core.models import Comment
from core.forms import CommentForm

class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        qs = Project.objects.filter(is_approved=True).select_related('submitted_by')
        
        # Filtering
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        
        language = self.request.GET.get('language')
        if language:
            qs = qs.filter(language__iexact=language)
        
        if self.request.GET.get('hot'):
            qs = qs.filter(is_hot=True)
            
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['-created_at', '-stars_count', 'name']:
            qs = qs.order_by(sort)
            
        return qs

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        from django.db.models import F
        obj = super().get_object(queryset)
        # atomic increment
        Project.objects.filter(pk=obj.pk).update(view_count=F('view_count') + 1)
        obj.refresh_from_db(fields=['view_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Prefetch
        
        # Comments with prefetch for replies
        content_type = ContentType.objects.get_for_model(Project)
        context['comments'] = Comment.objects.filter(
            content_type=content_type, 
            object_id=self.object.id,
            parent__isnull=True 
        ).select_related('author').prefetch_related(
            Prefetch('replies', queryset=Comment.objects.select_related('author'))
        ).order_by('created_at')
        
        context['comment_form'] = CommentForm()
        return context

class ProjectSubmitView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')
    
    def get_template_names(self):
        if self.request.htmx:
            return ['projects/project_submit_partial.html']
        return ['projects/project_form.html']
    
    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        response = super().form_valid(form)
        
        # Trigger immediate sync
        try:
             from .utils import sync_project_metadata
             sync_project_metadata(self.object)
        except Exception:
             pass # Don't block submission if sync fails
             
        return response
