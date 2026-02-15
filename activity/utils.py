from django.contrib.contenttypes.models import ContentType
from .models import Action
import datetime
from django.utils import timezone

DEDUP_WINDOW_SECONDS = 60

def create_action(user, verb, target=None):
    # check for similar action made in the dedup window
    now = timezone.now()
    last_60_sec = now - datetime.timedelta(seconds=DEDUP_WINDOW_SECONDS)
    similar_actions = Action.objects.filter(user_id=user.id, verb=verb, created__gte=last_60_sec)
    
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar_actions.filter(target_ct=target_ct, target_id=target.id)
    else:
        # 4.3: Also dedup on (user, verb) when target is None
        similar_actions = similar_actions.filter(target_ct__isnull=True, target_id__isnull=True)
    
    if not similar_actions.exists():
        # no existing similar action found
        action = Action(user=user, verb=verb, target=target)
        action.save()
        return True
    return False
