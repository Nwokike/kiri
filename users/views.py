from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

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
        
        return context
