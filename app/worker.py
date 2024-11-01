"""
A module that contains useful tools for implementing background workers.
"""

import abc
from celery import shared_task
import json
import uuid
import logging

import subprocess32 as sp

logger = logging.getLogger(__name__)


class Worker(object):
    """
    A base class for all workers.
    This will pull jobs from the beanstalk queue.
    It does not yet update the database with pending status and the
    like but could in the future.
    Currently it only logs what it is doing.
    To use this it should be subclassed and the process method should be
    implemented.
    This will ignore the result of the process method as the
    process is expected to save things itself.
    """

    __metaclass__ = abc.ABCMeta

    # Change logging configuration, added 2021-07-22
    logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

    def __init__(self, config, **kwargs):
        """
        Create a new Worker. This uses the config dictionary to connect to
        the queue and worker. That dictionary must contain a cache dictionary
        with the keys connection to indicate the connection to use, timeout for
        the time in seconds until an object is expired in the cache.

        :config: A configuration dictionary. This must specify the cache and
        queue to use.
        :kwargs: Keyword arguments to set as attributes of this worker. If no
        name is given then a random UUID is generated as a name.
        """

        self.config = dict(config)
        self.worker = self.config['worker']

        # Celery automatically connects to the broker defined in config
        self.queue = self.config['worker']['queue']  # Queue name

        # Generate a unique name for this worker instance if not provided
        self.name = kwargs.get('name', str(uuid.uuid4()))

        # self.beanstalk = beanstalkc.Connection(**config['queue']['connection'])
        # self.beanstalk.watch(config['worker']['queue'])
        # self.beanstalk.ignore('default')

        self.name = kwargs.get('name', str(uuid.uuid4()))
        self.logger = logging.getLogger('worker.Worker.%s' % self.name)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def models(self, type, version, file='all.txt'):
        """
        A method to return the path to a given type, and version's all.txt

        :param str type: The type, should be one of IL, HL.
        :param str version: The version string to use.
        :returns: The full path to the all.txt file for those models.
        """
        return '{base}/{type}/{version}/lib/{file}'.format(
            base=self.config['models'], type=type, version=version, file=file)

    def execute(self, *args, **kwargs):
        """
        Run a shell command and check the result of call.

        :*args: A list of arguments for the shell command. They are as
        check_call.
        :**kwargs: Keyword arguments as for check_call. If no timeout is not
        given then the default timeout is used.
        :returns: None.
        """

        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.worker.get('timeout', 60)

        self.logger.info("Running command %s", args)
        result = sp.check_call(args, **kwargs)
        self.logger.info("Command Finished")
        return result

    def store(self, job, result):
        """
        Store the result of a job.
        Currently this does nothing as the jar3d jar stores in the database.

        :param dict job: The job that was processed.
        :param obj result: The result to store.
        """
        pass

    @abc.abstractmethod
    def work(self, job):
        """
        Process the data. This method takes the input query which was placed
        in the queue and performs some operation to create the result data
        structure. In addition, the state of the job will be updated. If this
        process fails it should raise an exception to indicate failure. All
        worker subclasses must implement this.

        :param dict job: The job to process.
        :returns: None.
        """
        pass

    def mark(self, job, status='succeeded'):
        """
        Mark a job status in the database.
        """
        pass

    # def __call__(self):
    #     """
    #     The main entry point for all workers. When called this will wait
    #     until a job can be reserved from the queue and then send it to
    #     self.work(). The jobs body's are expected to be JSON encoded
    #     dictionaries.
    #     """

    #     self.logger.info("Starting worker %s", self.name)

    #     while True:
    #         job = self.beanstalk.reserve()
    #         job.bury()

    #         try:
    #             current = json.loads(job.body)
    #             self.logger.info("Working on current %s", current['id'])
    #             self.mark(current, status='pending')
    #             self.work(current)
    #             self.logger.info("Done working on %s", current['id'])
    #             self.mark(job, status='succeeded')
    #         except sp.TimeoutExpired as err:
    #             self.logger.error("Job ran too long: %s", current['id'])
    #             self.mark(current, status='timeout')
    #         except Exception as err:
    #             self.logger.error("Error working with %s", current['id'])
    #             self.logger.exception(err)
    #             self.mark(current, status='failed')
    #         finally:
    #             job.delete()



    @shared_task(bind=True, name='my_worker_task')
    def my_worker_task(self, current):
        """
        Celery task that processes a job and handles errors and logging.
        """
        try:
            logger.info("Working on current %s", current['id'])

            # Mark job as pending
            self.mark(current, status='pending')

            # Perform the actual work
            self.work(current)

            # Mark job as succeeded
            logger.info("Done working on %s", current['id'])
            self.mark(current, status='succeeded')

        except sp.TimeoutExpired as err:
            logger.error("Job ran too long: %s", current['id'])
            self.mark(current, status='timeout')

        except Exception as err:
            logger.error("Error working with %s", current['id'])
            logger.exception(err)
            self.mark(current, status='failed')
