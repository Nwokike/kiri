from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from .models import Publication
from .forms import PublicationForm
from core.models import Comment
from core.forms import CommentForm
from projects.services import GitHubService
import logging

logger = logging.getLogger(__name__)

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
        
        # Fetch Content from GitHub if configured
        if self.object.github_repo_url and self.object.github_file_path:
            try:
                # We reuse the GitHubService to fetch raw file content
                # Need to parse owner/repo from URL
                parsed = GitHubService.parse_repo_url(self.object.github_repo_url)
                if parsed:
                    owner, repo = parsed
                    # Using the cached fetch mechanism would be ideal, but for now direct fetch
                    # We can use the gist_service's helper or add a new one. 
                    # Let's trust GitHubService has what we need or add a quick fetch here using requests
                    # actually, let's use the helper we added to GistService or similar.
                    # GitHubService.fetch_structure is for trees. 
                    # Let's add simple request here for robustness or use GistService helper if accessible?
                    # Better: Implement proper fetching in get_context_data
                    import requests
                    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{self.object.github_file_path}"
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        context['github_content'] = resp.text
                    else:
                        context['github_error'] = f"Failed to load content from GitHub ({resp.status_code})"
            except Exception as e:
                logger.error(f"Error fetching publication content: {e}")
                context['github_error'] = "Error loading remote content"
        
        # Comments context
        content_type = ContentType.objects.get_for_model(Publication)
        
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

class PublicationImportLandingView(LoginRequiredMixin, ListView):
    template_name = 'publications/import_landing.html'
    context_object_name = 'repos'

    def get_queryset(self):
        return [] # Fetched via API

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from users.models import UserIntegration
        integrations = UserIntegration.objects.filter(user=self.request.user)
        connected_map = {i.platform: i for i in integrations}
        
        context['platforms'] = [
            {'name': 'GitHub', 'icon': 'fab fa-github', 'connected': connected_map.get('github'), 'connect_url': '/accounts/github/login/?process=connect'},
            {'name': 'GitLab', 'icon': 'fab fa-gitlab', 'connected': connected_map.get('gitlab'), 'connect_url': '/accounts/gitlab/login/?process=connect'},
            {'name': 'Bitbucket', 'icon': 'fab fa-bitbucket', 'connected': connected_map.get('bitbucket'), 'connect_url': '/accounts/bitbucket_oauth2/login/?process=connect'},
        ]
        return context

class PublicationCreateView(LoginRequiredMixin, CreateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'publications/publication_form.html'
    success_url = reverse_lazy('publications:list')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('import_mode'):
            initial['github_repo_url'] = self.request.GET.get('repo_url')
            # Look for common READMEs/Papers if not specified
            # Note: We will handle file selection in the template via JS
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PublicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'publications/publication_form.html'
    
    def test_func(self):
        pub = self.get_object()
        return self.request.user == pub.author

    def get_success_url(self):
        return reverse_lazy('publications:detail', kwargs={'slug': self.object.slug})
