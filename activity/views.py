from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Action

class FeedView(LoginRequiredMixin, ListView):
    model = Action
    template_name = 'activity/feed.html'
    context_object_name = 'actions'
    paginate_by = 25

    def get_queryset(self):
        # 5.1: If following is empty, user only sees their own actions.
        following_ids = self.request.user.rel_from_set.values_list('user_to_id', flat=True)
        return Action.objects.filter(
            user_id__in=list(following_ids) + [self.request.user.id]
        ).select_related('user', 'target_ct')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actions = context['actions']
        
        # 4.1: Bulk-resolve Generic Foreign Keys to avoid N+1
        # 1. Group target IDs by ContentType
        targets_by_ct = {}
        for action in actions:
            if action.target_ct_id and action.target_id:
                targets_by_ct.setdefault(action.target_ct_id, []).append(action.target_id)
        
        # 2. Fetch actual objects in bulk for each ContentType
        from django.contrib.contenttypes.models import ContentType
        resolved_objects = {}
        for ct_id, ids in targets_by_ct.items():
            ct = ContentType.objects.get_for_id(ct_id)
            model_class = ct.model_class()
            if model_class:
                objs = model_class.objects.in_bulk(ids)
                resolved_objects[ct_id] = objs
                
        # 3. Attach objects back to actions (using a cached_target attribute to avoid triggering GFK descriptor)
        for action in actions:
            if action.target_ct_id and action.target_id:
                action.bulk_target = resolved_objects.get(action.target_ct_id, {}).get(action.target_id)
            else:
                action.bulk_target = None
                
        return context
