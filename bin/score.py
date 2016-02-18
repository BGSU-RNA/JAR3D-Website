#!/usr/bin/env python

"""This is a background working for scoring a query against all jar3d motifs.
"""

import os

import subprocess32 as sp

from JAR3Doutput.worker import Worker
from JAR3Doutput import settings


class ScoringWorker(Worker):
    def process(self, query):
        here = os.path.dirname(__file__)
        command = ['java', '-Xmx500m', '-jar',
                   os.path.normalize(here, self.worker['jar']),
                   self.config['models']['il'],
                   self.config['config']['hl'],
                   query['id'],
                   self.config['db']['user'],
                   self.config['db']['password'],
                   self.config['db']['database']]
        sp.check_call(command, timeout=self.worker['timeout'])

if __name__ == '__main__':
    config = {
        'queue': settings.QUEUE,
        'worker': settings.WORKERS['scoring'],
        'models': {
            'il': os.path.join(settings.MODELS, 'il'),
            'hl': os.path.join(settings.MODELS, 'hl'),
        },
        'db': {
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'database': settings.DATABASES['default']['DATABASE'],
        },
    }
    worker = ScoringWorker(config)
    worker()
