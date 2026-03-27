from django.core.management.base import BaseCommand
from kiri_project.tasks import sync_github_stats

class Command(BaseCommand):
    help = 'Enqueue GitHub Stats Sync Task via Django async tasks'

    def handle(self, *args, **kwargs):
        self.stdout.write("Enqueuing GitHub Stats Sync...")
        try:
            sync_github_stats.enqueue()
            self.stdout.write(self.style.SUCCESS("Successfully enqueued task."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to enqueue task: {e}"))
