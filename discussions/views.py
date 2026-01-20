from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .models import Topic, Reply
from .forms import TopicForm, ReplyForm

class TopicListView(ListView):
    model = Topic
    template_name = 'discussions/topic_list.html'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

class TopicDetailView(DetailView):
    model = Topic
    template_name = 'discussions/topic_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reply_form'] = ReplyForm()
        # Increment view count
        self.object.view_count += 1
        self.object.save(update_fields=['view_count'])
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
