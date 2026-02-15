from django.core.management.base import BaseCommand
from kiri_project.tasks import (
    update_project_hot_status, 
    backup_db_to_r2, 
    sync_github_stats, 
    cleanup_tmp_files
)

class Command(BaseCommand):
    help = 'Runs periodic background tasks natively. Integrated with django.tasks (Django 6.0).'

    def add_arguments(self, parser):
        parser.add_argument('--daily', action='store_true', help='Run daily tasks (Hot status, Backups)')
        parser.add_argument('--hourly', action='store_true', help='Run hourly tasks (Cleanup)')
        parser.add_argument('--frequent', action='store_true', help='Run frequent tasks (GitHub sync)')

    def handle(self, *args, **options):
        if options['daily']:
            self.stdout.write("Scheduling daily tasks...")
            update_project_hot_status.enqueue()
            backup_db_to_r2.enqueue()
        
        if options['hourly']:
            self.stdout.write("Scheduling hourly tasks...")
            cleanup_tmp_files.enqueue()
            
        if options['frequent']:
            self.stdout.write("Scheduling frequent tasks (30-min intervals)...")
            sync_github_stats.enqueue()
            
        if not any([options['daily'], options['hourly'], options['frequent']]):
            self.stdout.write(self.style.WARNING("No interval specified. Use --daily, --hourly, or --frequent."))
        else:
            self.stdout.write(self.style.SUCCESS("Tasks enqueued successfully."))
