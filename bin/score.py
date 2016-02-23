#!/usr/bin/env python

"""This is a background working for scoring a query against all jar3d motifs.
The JAR3Doutput folder should be in the PYTHONPATH.
"""

import os
import logging

from JAR3Doutput.worker import Worker
from JAR3Doutput import settings

HERE = os.path.dirname(__file__)


class ScoringWorker(Worker):
    """The worker to score a loop against all models.
    """

    def work(self, job):
        """Process the job by calling the jar3d jar file for the given job.

        :param dict job: A job specifying the job id and and the version.
        """

        jar = os.path.abspath(os.path.join(HERE, self.worker['jar']))
        return self.execute('java', '-Xmx500m', '-jar',
                            jar,
                            self.models('IL', job['version']),
                            self.models('HL', job['version']),
                            job['id'],
                            self.config['db']['user'],
                            self.config['db']['password'],
                            self.config['db']['database'])

if __name__ == '__main__':
    config = {
        'queue': settings.QUEUE,
        'worker': settings.WORKERS['score'],
        'models': os.path.join(settings.MODELS),
        'db': {
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'database': settings.DATABASES['default']['NAME'],
        },
    }
    logging.basicConfig()
    worker = ScoringWorker(config)
    worker()
