from django.views.generic import DetailView, TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, login_not_required
from .models import UserIntegration

User = get_user_model()

@method_decorator(login_not_required, name='dispatch')
class UserProfileDetailView(DetailView):
    model = User
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        # 5.3: Staff users can view all profiles for moderation/support.
        # This bypasses the is_profile_public restriction.
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

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from .models import Contact

@require_POST
def follow_user(request, username):
    """HTMX view to follow a user."""
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        _, created = Contact.objects.get_or_create(user_from=request.user, user_to=user_to_follow)
        if created:
            try:
                from activity.utils import create_action
                create_action(request.user, 'followed', user_to_follow)
            except Exception:
                pass
    
    if request.htmx:
        return HttpResponse('<button class="btn btn-secondary" hx-post="' + 
                            f'/nexus/unfollow/{username}/' + '" hx-swap="outerHTML">Unfollow</button>')
    return JsonResponse({'status': 'following'})

@require_POST
def unfollow_user(request, username):
    """HTMX view to unfollow a user."""
    user_to_unfollow = get_object_or_404(User, username=username)
    Contact.objects.filter(user_from=request.user, user_to=user_to_unfollow).delete()
    
    if request.htmx:
        return HttpResponse('<button class="btn btn-primary" hx-post="' + 
                            f'/nexus/follow/{username}/' + '" hx-swap="outerHTML">Follow</button>')
    return JsonResponse({'status': 'unfollowed'})

