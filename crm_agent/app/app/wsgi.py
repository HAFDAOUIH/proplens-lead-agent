"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Ensure the project root that contains the `crm_agent` package is on sys.path
PROJECT_ROOT_PARENT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PARENT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

application = get_wsgi_application()
