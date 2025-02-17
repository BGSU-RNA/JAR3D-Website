#!/usr/bin/env python

"""
A worker to align a series of loops to a model.
"""

import os
import logging

from app.worker import Worker
from config import settings

HERE = os.path.dirname(__file__)


class AlignWorker(Worker):
    """The worker to align against a model.
    """

    def work(self, job):
        """Run the aligning jar file on the job.

        :param dict job: The job to run.
        """

        models = self.models(job['motif_group'][0:2], job['version'], file='')
        jar = os.path.abspath(os.path.join(HERE, self.worker['jar']))

        return self.execute('java', '-Xmx500m', '-jar',
                            jar,
                            models,
                            job['motif_group'],
                            job['id'],
                            job['loop_id'],
                            self.config['db']['user'],
                            self.config['db']['password'],
                            self.config['db']['database'])

if __name__ == '__main__':
    config = {
        'queue': settings.QUEUE,
        'worker': settings.WORKERS['align'],
        'models': os.path.join(settings.MODELS),
        'db': {
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'database': settings.DATABASES['default']['NAME'],
        },
    }
    level = settings.WORKERS['align'].get('log_level', logging.INFO)
    logging.basicConfig(level=level)
    worker = AlignWorker(config)
    worker()
