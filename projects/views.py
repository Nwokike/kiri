from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Project
from .forms import ProjectSubmissionForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Restrict access to staff users."""
    def test_func(self):
        return self.request.user.is_staff


# ── Public Views ──

@method_decorator(login_not_required, name='dispatch')
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        qs = Project.objects.all()

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        # Search
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Project.Category.choices
        context['statuses'] = Project.Status.choices
        context['current_category'] = self.request.GET.get('category', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


@method_decorator(login_not_required, name='dispatch')
class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'


# ── Staff Views ──

class ProjectSubmitView(StaffRequiredMixin, CreateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_submit.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"'{self.object.name}' added successfully!",
        )
        return response

class ProjectUpdateView(StaffRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_submit.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"'{self.object.name}' updated successfully!",
        )
        return response

class ProjectPostFacebookView(StaffRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        from kiri_project.tasks import post_to_facebook
        from .models import Project
        try:
            project = Project.objects.get(slug=slug)
            post_to_facebook('project', project.id)
            messages.success(request, f"Facebook post task for '{project.name}' has been queued.")
        except Project.DoesNotExist:
            messages.error(request, "Project not found.")
        return redirect('projects:detail', slug=slug)

