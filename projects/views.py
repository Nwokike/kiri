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
        return Project.objects.filter(is_approved=True).order_by('-created_at')

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Comments
        content_type = ContentType.objects.get_for_model(Project)
        context['comments'] = Comment.objects.filter(
            content_type=content_type, 
            object_id=self.object.id,
            parent__isnull=True # Top level comments
        ).order_by('created_at')
        context['comment_form'] = CommentForm()
        return context

class ProjectSubmitView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')
    
    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        return super().form_valid(form)
