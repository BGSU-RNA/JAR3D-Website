
from celery import Celery
import os
import sys

# Add the project directory to the Python path
sys.path.append('/var/www/jar3d')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'


from app.my_queue import score, align

# test_import.py
try:
    from queue import Queue
    print("Import successful!")
except ImportError as e:
    print(f"Import error: {e}")


job_data = {'id': 123, 'task': 'test scoring'}  # Sample job data

# Dispatch the task to the Celery queue
score(job_data)

# You should see the worker pick up the task in the worker logs
