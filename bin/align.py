#!/usr/bin/env python

import os
import sys
import logging

import subprocess32 as sp

HERE = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(HERE, "..")))

from JAR3Doutput.worker import Worker
from JAR3Doutput import settings


class AlignWorker(Worker):
    def process(self, query):
        here = os.path.dirname(__file__)
        print('Processing %s' % query)

        models = self.models(query['motif_group'][0:2], query['version'])
        command = ['java', '-Xmx500m', '-jar',
                   os.path.abspath(os.path.join(here, self.worker['jar'])),
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
        'models': os.path.join(settings.MODELS),
        'db': {
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'database': settings.DATABASES['default']['NAME'],
        },
    }
    logging.basicConfig()
    worker = AlignWorker(config)
    worker()
