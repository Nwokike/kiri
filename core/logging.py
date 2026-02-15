import logging
from django.core.exceptions import DisallowedHost

class DisallowedHostFilter(logging.Filter):
    """
    Filter that silences DisallowedHost exceptions in logs.
    These are usually caused by bots and script kiddies.
    """
    def filter(self, record):
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            if issubclass(exc_type, DisallowedHost):
                return False
        
        # Also catch the error message if it's already formatted
        if "Invalid HTTP_HOST header" in record.getMessage():
            return False
            
        return True
