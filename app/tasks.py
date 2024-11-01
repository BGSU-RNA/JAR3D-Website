from celery import shared_task

@shared_task
def score_task(job):
    # Process the scoring job
    pass

@shared_task
def align_task(job):
    # Process the alignment job
    pass
