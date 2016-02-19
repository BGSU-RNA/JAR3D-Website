import json

import beanstalkc

from JAR3Doutput import settings


def queue(tube, job):
    beanstalk = beanstalkc.Connection(**settings.QUEUE['connection'])
    beanstalk.use(tube)
    beanstalk.put(json.dumps(job))


def score(job):
    queue(settings.WORKERS['score']['queue'], job)


def align(job):
    queue(settings.WORKERS['align']['queue'], job)
