from django.core.management.base import BaseCommand
from kiri_project.tasks import sync_publications

class Command(BaseCommand):
    help = 'Enqueue Publications Sync Task via Django async tasks'

    def handle(self, *args, **kwargs):
        self.stdout.write("Enqueuing Publications Sync...")
        try:
            sync_publications.enqueue()
            self.stdout.write(self.style.SUCCESS("Successfully enqueued task."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to enqueue task: {e}"))
