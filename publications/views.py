from django.views import View
from django.views.generic import ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .models import Publication
from kiri_project.tasks import sync_publications

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

@method_decorator(login_not_required, name='dispatch')
class PublicationListView(ListView):
    model = Publication
    template_name = 'publications/publication_list.html'
    context_object_name = 'publications'
    paginate_by = 12

@method_decorator(login_not_required, name='dispatch')
class PublicationDetailView(DetailView):
    model = Publication
    template_name = 'publications/publication_detail.html'
    context_object_name = 'publication'

class PublicationDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Publication
    success_url = reverse_lazy('publications:list')
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Publication '{obj.title}' deleted successfully.")
        return super().delete(request, *args, **kwargs)

class PublicationSyncView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        sync_publications()
        messages.success(request, "Organization sync triggered successfully. Publications updated.")
        return redirect('publications:list')

class PublicationPostFacebookView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        from kiri_project.tasks import post_to_facebook
        try:
            pub = Publication.objects.get(slug=slug)
            post_to_facebook('publication', pub.id)
            messages.success(request, f"Facebook post task for '{pub.title}' has been queued.")
        except Publication.DoesNotExist:
            messages.error(request, "Publication not found.")
        return redirect('publications:detail', slug=slug)


