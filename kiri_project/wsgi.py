# WSGI config for Kiri Research Labs.

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiri_project.settings')

application = get_wsgi_application()
