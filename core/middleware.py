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
                message=str(exception),
                exception_type=type(exception).__name__,
                traceback=traceback.format_exc(),
                user=user
            )
        except Exception as e:
            # Fallback to standard logging if ErrorLog creation fails
            logger.error(f"Failed to create ErrorLog for exception: {e}")
            logger.error(traceback.format_exc())
        
        return None

class ContentSecurityPolicyMiddleware:
    """
    Middleware to add Content Security Policy headers.
    Native solution replacing django-csp.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # 4.6: Build CSP header from settings (Native implementation)
        csp_parts = []
        
        # Mapping of setting name to policy directive
        directives = {
            'CSP_DEFAULT_SRC': 'default-src',
            'CSP_SCRIPT_SRC': 'script-src',
            'CSP_STYLE_SRC': 'style-src',
            'CSP_FONT_SRC': 'font-src',
            'CSP_IMG_SRC': 'img-src',
            'CSP_CONNECT_SRC': 'connect-src',
            'CSP_FRAME_SRC': 'frame-src',
            'CSP_OBJECT_SRC': 'object-src',
        }
        
        for setting_name, directive in directives.items():
            value = getattr(settings, setting_name, None)
            if value:
                # Value is expected to be a tuple/list of strings
                csp_parts.append(f"{directive} {' '.join(value)}")
        
        if csp_parts:
            # Check if it was already set (e.g. by another middleware)
            if 'Content-Security-Policy' not in response:
                response['Content-Security-Policy'] = '; '.join(csp_parts)
            
        return response
