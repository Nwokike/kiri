from django.views.generic import ListView, CreateView, DetailView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import F
import logging

from .models import Project
from .forms import ProjectSubmissionForm
from users.models import UserIntegration
from .utils import sync_project_metadata

logger = logging.getLogger(__name__)


class StaffRequiredMixin(UserPassesTestMixin):
    """Staff-only access mixin."""
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
        # Session-based view count deduplication (#5)
        session_key = f'viewed_project_{obj.pk}'
        if not self.request.session.get(session_key):
            Project.objects.filter(pk=obj.pk).update(view_count=F('view_count') + 1)
            self.request.session[session_key] = True
            obj.refresh_from_db(fields=['view_count'])
        return obj


class ImportLandingView(StaffRequiredMixin, View):
    """Entry point for project import, showing platform status."""
    def get(self, request, *args, **kwargs):
        user = request.user
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
        return render(request, 'projects/import_landing.html', {'platforms': platforms})


class UserReposApiView(StaffRequiredMixin, View):
    """
    JSON API: Lists user repositories from GitHub/HuggingFace for dropdown import.
    GET /projects/api/user-repos/?platform=github
    """
    def get(self, request, *args, **kwargs):
        platform = request.GET.get('platform', 'github')
        integration = UserIntegration.objects.filter(user=request.user, platform=platform).first()
        
        if not integration:
            return JsonResponse({'error': f'Not connected to {platform}'}, status=403)
            
        token = integration.get_decrypted_access_token()
        if not token:
            return JsonResponse({'error': 'Invalid access token'}, status=403)
            
        try:
            if platform == 'github':
                from .services import GitHubService
                repos = GitHubService.fetch_user_repos(token)
            elif platform == 'huggingface':
                from .services import HuggingFaceService
                repos = HuggingFaceService.fetch_user_repos(token)
            else:
                return JsonResponse({'error': 'Unsupported platform'}, status=400)
                
            return JsonResponse({'repos': repos})
        except Exception as e:
            logger.error(f"UserReposApiView error: {e}")
            return JsonResponse({'error': 'Failed to fetch repositories'}, status=502)


class ProjectSubmitView(StaffRequiredMixin, CreateView):
    model = Project
    form_class = ProjectSubmissionForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('import_mode'):
            repo_url = self.request.GET.get('repo_url', '')
            initial['github_repo_url'] = repo_url
            initial['name'] = self.request.GET.get('name', '')
            initial['description'] = self.request.GET.get('description', '')
            initial['language'] = self.request.GET.get('language', '')
            # Clean/parse topics if coming as a string from JS
            topics_raw = self.request.GET.get('topics', '[]')
            try:
                import json
                topics_list = json.loads(topics_raw)
                if isinstance(topics_list, list):
                    initial['topics'] = ", ".join(str(t) for t in topics_list)
                else:
                    initial['topics'] = ""
            except (json.JSONDecodeError, ValueError, TypeError):
                initial['topics'] = ""
            
            # Route URL to proper field based on host
            if 'huggingface.co' in repo_url:
                initial['huggingface_url'] = repo_url
            else:
                initial['github_repo_url'] = repo_url
                
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
            logger.warning("Auto-sync failed for '%s': %s", self.object.name, e)
        
        from django.contrib import messages
        messages.success(
            self.request,
            f"'{self.object.name}' submitted! It will appear publicly after staff approval."
        )
        return response


class RepoFilesApiView(StaffRequiredMixin, View):
    """
    JSON API: Fetches the file structure of a GitHub repo.
    """
    def get(self, request, *args, **kwargs):
        repo_url = request.GET.get('url', '').strip()
        if not repo_url:
            return JsonResponse({'error': 'url required'}, status=400)

        from .services import GitHubService
        if not GitHubService.parse_repo_url(repo_url):
            return JsonResponse({'error': 'Invalid GitHub URL'}, status=400)

        try:
            data = GitHubService.fetch_structure(repo_url)
            return JsonResponse({'files': data.get('file_list', [])})
        except Exception as e:
            logger.warning("RepoFilesApiView error: %s", e)
            return JsonResponse({'error': 'Failed to fetch files'}, status=502)
