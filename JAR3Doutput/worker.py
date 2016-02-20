"""A module that contains useful tools for implementing background workers.
"""

import abc
import json
import uuid
import logging
import beanstalkc


class Worker(object):
    """A base class for all workers. This will pull jobs from the beanstalk
    queue. It does not yet update the databaase with pending status and the
    like but could in the future. Currently it only logs what it is doing. To
    use this it should be subclassed and the process method should be
    implemented. This will ignore the result of the process method as the
    process is expected to save things itself.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config, **kwargs):
        """Create a new Worker. This uses the config dictionary to connect to
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
        self.beanstalk = beanstalkc.Connection(**config['queue']['connection'])
        self.beanstalk.watch(config['worker']['queue'])
        self.beanstalk.ignore('default')

        self.name = kwargs.get('name', str(uuid.uuid4()))
        self.logger = logging.getLogger('queue.Worker:%s' % self.name)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def models(self, type, version):
        """A method to return the path to a given type, and version's all.txt

        :param str type: The type, should be one of IL, HL.
        :param str version: The version string to use.
        :returns: The full path to the all.txt file for those models.
        """
        return '{base}/{type}/{version}/lib/all.txt'.format(
            base=self.config['models'], type=type, version=version)

    @abc.abstractmethod
    def process(self, query):
        """Process the data. This method takes the input query which was placed
        in the queue and preforms some operation to create the result data
        structure. In addition, the state of the job will be updated. If this
        process fails it should raise an exception to indicate failure. All
        worker subclasses must implement this.

        :param dict query: The query to process.
        :returns: Nothing.
        """
        pass

    def work(self, job, query):
        """Work on a job. This will work on some job until it is finished. The
        job will be deleted from the queue if this finishes. The job's status
        will be set to pending while it is being processed and then to success
        if it succeeds.

        :param Job job: The job to work on.
        :param dict query: The query to work on.
        """

        self.logger.debug("Working on query %s", query['id'])
        self.process(query)
        self.logger.debug("Done working on %s", query['id'])

    def __call__(self):
        """The main entry point for all workers. When called this will wait
        until a job can be reserved from the queue and then send it to
        self.work(). The jobs body's are expected to be JSON encoded
        dictionaries.
        """

        self.logger.info("Starting worker %s", self.name)
        while True:
            job = self.beanstalk.reserve()
            print("Got job %s", job)
            job.bury()
            try:
                query = json.loads(job.body)
                self.work(job, query)
            except Exception as err:
                self.logger.error("Error working with %s", query['id'])
                self.logger.exception(err)
            finally:
                job.delete()
