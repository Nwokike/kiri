from django.views.generic import DetailView, TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import UserIntegration

User = get_user_model()

class UserProfileDetailView(DetailView):
    model = User
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        # Privacy: Allow owner to view private profile, otherwise only public
        qs = User.objects.all()
        if self.request.user.is_authenticated and self.request.user.is_staff:
             return qs 
        if self.request.user.is_authenticated and self.request.user.username == self.kwargs.get('username'):
             return qs
        return qs.filter(is_profile_public=True)

    def get_object(self):
        # Use get_queryset handling for privacy check
        return super().get_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object  # Already fetched by DetailView
        
        # Optimize queries - only fetch needed fields
        context['projects'] = user.projects.filter(
            is_approved=True
        ).only('name', 'slug', 'description', 'stars_count', 'language', 'is_hot').order_by('-stars_count')
        
        context['publications'] = user.authored_publications.filter(
            is_published=True
        ).only('title', 'slug', 'created_at', 'version').order_by('-created_at')
        
        context['contributions'] = user.contributed_publications.filter(
            is_published=True
        ).only('title', 'slug', 'created_at', 'version').order_by('-created_at')
        
        # Add integrations for owner view
        if self.request.user.is_authenticated and self.request.user == user:
            context['integrations'] = UserIntegration.objects.filter(user=user)
        
        return context


class IntegrationsView(LoginRequiredMixin, TemplateView):
    """User integrations settings page."""
    template_name = 'users/integrations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's connected integrations
        integrations = UserIntegration.objects.filter(user=self.request.user)
        connected = {i.platform: i for i in integrations}
        
        # Define all available platforms
        platforms = [
            {
                'id': 'github',
                'name': 'GitHub',
                'icon': 'fab fa-github',
                'description': 'Connect your GitHub account to import repos and sync stars',
                'connected': connected.get('github'),
                'connect_url': '/accounts/github/login/?process=connect',
            },
            {
                'id': 'gitlab',
                'name': 'GitLab',
                'icon': 'fab fa-gitlab',
                'description': 'Connect your GitLab account to import projects',
                'connected': connected.get('gitlab'),
                'connect_url': '/accounts/gitlab/login/?process=connect',
            },
            {
                'id': 'bitbucket',
                'name': 'Bitbucket',
                'icon': 'fab fa-bitbucket',
                'description': 'Connect your Bitbucket account to import repositories',
                'connected': connected.get('bitbucket'),
                'connect_url': '/accounts/bitbucket_oauth2/login/?process=connect',
            },
            {
                'id': 'huggingface',
                'name': 'Hugging Face',
                'icon': 'fas fa-robot',
                'description': 'Connect your Hugging Face account for ML models',
                'connected': connected.get('huggingface'),
                'connect_url': '/accounts/huggingface/login/?process=connect',
            },
        ]
        
        context['platforms'] = platforms
        context['integrations'] = integrations
        context['primary_integration'] = self.request.user.get_primary_integration()
        
        return context

