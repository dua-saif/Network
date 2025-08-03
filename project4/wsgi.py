"""
WSGI config for project4 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project4.settings')

application = get_wsgi_application()

import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError

User = get_user_model()

try:
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("Duasaif", "duasaif.atd@gmail.com", "1234sameed@")
        print("✅ Superuser created!")
except OperationalError:
    print("⚠ Database not ready yet — skipping superuser creation.")