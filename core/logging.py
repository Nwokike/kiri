import logging
from django.core.exceptions import DisallowedHost


class DisallowedHostFilter(logging.Filter):
    """
    Filter that silences DisallowedHost exceptions in logs.
    These are usually caused by bots and scanners.
    """
    def filter(self, record):
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type is not None and isinstance(exc_type, type) and issubclass(exc_type, DisallowedHost):
                return False

        if "Invalid HTTP_HOST header" in record.getMessage():
            return False

        return True
