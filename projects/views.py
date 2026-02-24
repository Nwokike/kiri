from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.db.models import F
import logging

from .models import Project
from .forms import ProjectSubmissionForm
from users.models import UserIntegration
from .utils import sync_project_metadata

logger = logging.getLogger(__name__)


# Reusable mixin — staff-only access
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


@method_decorator(login_not_required, name='dispatch')
class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        qs = Project.objects.filter(is_approved=True).select_related('submitted_by')

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Project.Category.choices
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context


@method_decorator(login_not_required, name='dispatch')
class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Project.objects.filter(pk=obj.pk).update(view_count=F('view_count') + 1)
        obj.refresh_from_db(fields=['view_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ImportLandingView(StaffRequiredMixin, ListView):
    template_name = 'projects/import_landing.html'
    context_object_name = 'repos'

    def get_queryset(self):
        return []  # Fetched via API client-side (api_repo_files endpoint)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        integrations = UserIntegration.objects.filter(user=user)
        connected_map = {i.platform: i for i in integrations}

        platforms = [
            {
                'id': 'github',
                'name': 'GitHub',
                'icon': 'fab fa-github',
                'connected': bool(connected_map.get('github')),
                'connect_url': reverse('github_login') + '?process=connect',
            },
            {
                'id': 'huggingface',
                'name': 'Hugging Face',
                'icon': 'fas fa-robot text-[#FFD21E]',
                'connected': bool(connected_map.get('huggingface')),
                'connect_url': reverse('huggingface_login') + '?process=connect',
            },
        ]
        context['platforms'] = platforms
        return context


class ProjectSubmitView(StaffRequiredMixin, CreateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('import_mode'):
            from .services import GitHubService
            repo_url = self.request.GET.get('repo_url', '')
            # Validate before pre-filling
            if repo_url and GitHubService.parse_repo_url(repo_url):
                initial['github_repo_url'] = repo_url
            initial['name'] = self.request.GET.get('name', '')
            initial['description'] = self.request.GET.get('description', '')
        return initial

    def get_template_names(self):
        if self.request.htmx:
            return ['projects/project_submit_partial.html']
        return ['projects/project_form.html']

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        response = super().form_valid(form)
        try:
            sync_project_metadata(self.object)
        except Exception as e:
            logger.warning("GitHub sync failed after project submit for '%s': %s", self.object.name, e)
        from django.contrib import messages
        messages.success(
            self.request,
            f"'{self.object.name}' submitted! It will appear publicly after staff approval."
        )
        return response


class RepoFilesApiView(LoginRequiredMixin, ListView):
    """
    JSON API: Fetches the file structure of a GitHub repo for the import landing.
    GET /projects/api/repo-files/?url=https://github.com/user/repo
    """
    def get(self, request, *args, **kwargs):
        repo_url = request.GET.get('url', '').strip()
        if not repo_url:
            return JsonResponse({'error': 'url parameter is required'}, status=400)

        from .services import GitHubService
        parsed = GitHubService.parse_repo_url(repo_url)
        if not parsed:
            return JsonResponse({'error': 'Invalid GitHub URL'}, status=400)

        try:
            data = GitHubService.fetch_structure(repo_url)
            return JsonResponse({'files': data.get('file_list', [])})
        except Exception as e:
            logger.warning("RepoFilesApiView error for %s: %s", repo_url, e)
            return JsonResponse({'error': 'Failed to fetch repository files'}, status=502)
