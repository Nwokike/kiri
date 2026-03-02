import traceback
import logging
from django.conf import settings
from .models import ErrorLog

logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware:
    """
    Middleware to capture uncaught exceptions and log them to the ErrorLog model.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            user = request.user if request.user.is_authenticated else None
            
            ErrorLog.objects.create(
                level='error',
                path=request.path,
                method=request.method,
                message=str(exception),
                exception_type=type(exception).__name__,
                traceback=traceback.format_exc(),
                user=user,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except Exception as e:
            logger.error(f"Failed to create ErrorLog for exception: {e}")
            logger.error(traceback.format_exc())
        
        return None
