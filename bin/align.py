#!/usr/bin/env python

import os

import subprocess32 as sp

from JAR3Doutput.worker import Worker
from JAR3Doutput import settings


class AlignWorker(Worker):
    def process(self, query):
        here = os.path.dirname(__file__)

        models = self.config['models']['il']
        if query['motif_group'].startswith('HL'):
            models = self.config['models']['hl']

        command = ['java', '-Xmx500m', '-jar',
                   os.path.normalize(here, self.worker['jar']),
                   models,
                   query['motif_group'],
                   query['id'],
                   query['loop_id'],
                   self.config['db']['user'],
                   self.config['db']['password'],
                   self.config['db']['database']]

        sp.check_call(command, timeout=self.worker['timeout'])

if __name__ == '__main__':
    config = {
        'queue': settings.QUEUE,
        'worker': settings.WORKERS['align'],
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
    worker = AlignWorker(config)
    worker()
