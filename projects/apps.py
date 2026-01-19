from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    
    def ready(self):
        # Import signal handlers for gist cleanup on project deletion
        from django.db.models.signals import post_delete
        from .models import Project
        
        def cleanup_project_gist(sender, instance, **kwargs):
            """Delete associated GitHub gist when project is deleted."""
            if instance.gist_id:
                try:
                    from .gist_service import GistService
                    GistService.delete_gist(instance.gist_id)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to delete gist {instance.gist_id}: {e}")
        
        post_delete.connect(cleanup_project_gist, sender=Project)

