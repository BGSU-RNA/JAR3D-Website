import json

from config import settings
from app.tasks import score_task, align_task  # Import Celery tasks

def queue(tube, job):
    """
    Dispatch job to the appropriate Celery queue.
    """
    # Since `tube` is essentially the queue name in Celery, you can use it directly
    if tube == settings.WORKERS['score']['queue']:
        score_task.apply_async(args=[job], queue=tube)
    elif tube == settings.WORKERS['align']['queue']:
        align_task.apply_async(args=[job], queue=tube)

def score(job):
    """
    Dispatch the score job to the Celery queue.
    """
    return queue(settings.WORKERS['score']['queue'], job)

def align(job):
    """
    Dispatch the align job to the Celery queue.
    """
    return queue(settings.WORKERS['align']['queue'], job)
