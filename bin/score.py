#!/usr/bin/env python

"""This is a background working for scoring a query against all jar3d motifs.
"""

import os
import sys
import logging

import subprocess32 as sp

HERE = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(HERE, "..")))

from JAR3Doutput.worker import Worker
from JAR3Doutput import settings


class ScoringWorker(Worker):
    def process(self, query):
        """Process the query by calling the jar3d jar file for the given job.

        :param dict query: A query specifying the query id and and the version.
        """

        il_models = self.models('IL', query['version'])
        hl_models = self.models('HL', query['version'])
        command = ['java', '-Xmx500m', '-jar',
                   os.path.abspath(os.path.join(HERE, self.worker['jar'])),
                   il_models,
                   hl_models,
                   query['id'],
                   self.config['db']['user'],
                   self.config['db']['password'],
                   self.config['db']['database']]
        sp.check_call(command, timeout=self.worker['timeout'])

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
