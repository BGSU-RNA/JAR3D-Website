# not planning to use this at the moment
# trying to just run jobs synchronously

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jar3d.settings')

app = Celery('jar3d')

# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
