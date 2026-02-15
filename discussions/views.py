from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import F
from .models import Topic, Reply
from .forms import TopicForm, ReplyForm

@method_decorator(login_not_required, name='dispatch')
class TopicListView(ListView):
    model = Topic
    template_name = 'discussions/topic_list.html'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Topic.objects.all().select_related('author')
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        
        # 4.2: Filter closed topics if needed (default to visible but can toggle)
        if self.request.GET.get('active_only'):
            qs = qs.filter(is_closed=False)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = Topic.CATEGORY_CHOICES
        return context

@method_decorator(login_not_required, name='dispatch')
class TopicDetailView(DetailView):
    model = Topic
    template_name = 'discussions/topic_detail.html'
    
    def get_queryset(self):
        return Topic.objects.all().select_related('author').prefetch_related('replies__author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reply_form'] = ReplyForm()
        
        # 3.2: Atomic View Count Increment
        Topic.objects.filter(pk=self.object.pk).update(view_count=F('view_count') + 1)
        self.object.refresh_from_db(fields=['view_count'])
        
        return context
        
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        self.object = self.get_object()
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic = self.object
            reply.author = request.user
            reply.save()
            return redirect('discussions:detail', slug=self.object.slug)
        return self.render_to_response(self.get_context_data(reply_form=form))

class TopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    form_class = TopicForm
    template_name = 'discussions/topic_form.html'
    success_url = reverse_lazy('discussions:list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Record activity
        from activity.utils import create_action
        create_action(self.request.user, 'started a discussion', self.object)
        return response

def mark_solution_api(request, reply_id):
    """API view to mark a reply as the solution."""
    
    reply = get_object_or_404(Reply, pk=reply_id)
    
    # Only the topic author can mark a solution
    if request.user != reply.topic.author:
        return JsonResponse({'error': 'Only the author can mark a solution'}, status=403)
    
    # Unmark any existing solution for this topic
    reply.topic.replies.filter(is_solution=True).update(is_solution=False)
    
    reply.is_solution = True
    reply.save()
    
    return JsonResponse({'status': 'ok'})
