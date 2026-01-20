from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Action

class FeedView(LoginRequiredMixin, ListView):
    model = Action
    template_name = 'activity/feed.html'
    context_object_name = 'actions'
    paginate_by = 25

    def get_queryset(self):
        # Return actions from people the user follows plus their own actions?
        # Typically "Follow Feed" is actions of people I follow.
        # "Platform Feed" is global (maybe restricted?)
        # Let's do a mix or just global for now if it's small, but usually Follow based.
        
        # Get users being followed
        following_ids = self.request.user.rel_from_set.values_list('user_to_id', flat=True)
        # Include self in the feed? Usually yes or no. Let's say yes.
        return Action.objects.filter(user_id__in=list(following_ids) + [self.request.user.id]).select_related('user', 'target_ct')
