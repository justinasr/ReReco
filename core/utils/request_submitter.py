"""
Module that has all classes used for request submission to computing
"""
import logging
import time
from threading import Thread
from queue import Queue, Empty
from core.utils.ssh_executor import SSHExecutor
from core.utils.locker import Locker
from core.database.database import Database


class Worker(Thread):
    """
    A single worker thread that loops and submits requests from the queue
    """

    def __init__(self, name, task_queue):
        Thread.__init__(self)
        self.name = name
        self.queue = task_queue
        self.logger = logging.getLogger()
        self.logger.debug('Worker "%s" is being created', self.name)
        self.job_name = None
        self.job_start_time = None
        self.running = True
        self.start()

    def run(self):
        self.logger.debug('Worker "%s" is waiting for tasks', self.name)
        while self.running:
            try:
                func, job_name, args, kargs = self.queue.get(timeout=2)
                self.job_name = job_name
                self.job_start_time = time.time()
                self.logger.debug('Worker "%s" got a task. Queue size %s',
                                  self.name,
                                  self.queue.qsize())
                try:
                    func(*args, **kargs)
                except Exception as ex:
                    self.logger.error(ex)
                finally:
                    self.logger.debug('Worker "%s" has finished a task. Queue size %s',
                                      self.name,
                                      self.queue.qsize())
                    self.job_name = None
                    self.job_start_time = 0
            except Empty:
                # self.logger.debug('Worker "%s" did not get a task and is sad', self.name)
                self.job_name = None
                self.job_start_time = 0

    def join(self, timeout=None):
        self.running = False
        self.logger.debug('Joining the "%s" thread', self.name)
        Thread.join(self, timeout)


class WorkerPool:
    """
    Pool that contains all worker threads
    """

    def __init__(self, workers_count, task_queue):
        self.logger = logging.getLogger()
        self.workers = []
        for i in range(workers_count):
            self.logger.info('Creating a worker')
            worker = Worker(f'worker-{i}', task_queue)
            self.workers.append(worker)

    def get_worker_status(self):
        """
        Return a dictionary where keys are worker names and values are dictionaries
        of job names and time in seconds that job has been running for (if any)
        """
        status = {}
        now = time.time()
        for worker in self.workers:
            job_time = int(now - worker.job_start_time if worker.job_name else 0)
            status[worker.name] = {'job_name': worker.job_name,
                                   'job_time': job_time}

        return status


class RequestSubmitter:
    """
    Request submitter has a reference to the whole worker pool as well as job queue
    """

    # A FIFO queue. maxsize is an integer that sets the upperbound
    # limit on the number of items that can be placed in the queue.
    # If maxsize is less than or equal to zero, the queue size is infinite.
    __task_queue = Queue(maxsize=0)
    # All worker threads
    __worker_pool = WorkerPool(workers_count=2, task_queue=__task_queue)

    def __init__(self):
        self.logger = logging.getLogger()

    def add_request(self, request, controller):
        """
        Add request to submission queue
        """
        prepid = request.get_prepid()
        for task in list(RequestSubmitter.__task_queue.queue):
            if task[1] == prepid:
                raise Exception(f'Task "%s" is already in the queue')

        for worker, worker_info in RequestSubmitter.__worker_pool.get_worker_status().items():
            if worker_info['job_name'] == prepid:
                raise Exception(f'Task "{prepid}" is being worked on by "{worker}"')

        self.logger.info('Adding a task "%s". Queue size %s', prepid, self.get_queue_size())
        RequestSubmitter.__task_queue.put((self.submit_request, prepid, [request, controller], {}))

    def get_queue_size(self):
        """
        Return size of submission queue
        """
        return RequestSubmitter.__task_queue.qsize()

    def get_worker_status(self):
        """
        Return dictionary of all worker statuses
        """
        return RequestSubmitter.__worker_pool.get_worker_status()

    def submit_request(self, request, controller):
        """
        Method that is used by submission workers. This is where the actual submission happens
        """
        ssh_executor = SSHExecutor('lxplus.cern.ch', '/home/jrumsevi/auth.txt')
        prepid = request.get_prepid()
        with Locker().get_lock(prepid):
            request_db = Database('requests')
            request = controller.get(prepid)
            if request.get('status') != 'approved':
                raise Exception(f'Cannot submit a request with status {request.get("status")}')

            request.set('status', 'submitting')
            request_db.save(request.get_json())
            request = controller.get(prepid)
            self.logger.info('Locked %s for submission', prepid)
            ssh_executor.execute_command([f'rm -rf rereco_submission/{prepid}',
                                          f'mkdir -p rereco_submission/{prepid}'])
            with open(f'/tmp/{prepid}.sh', 'w') as temp_file:
                temp_file.write(controller.get_cmsdriver(request))

            ssh_executor.upload_file(f'/tmp/{prepid}.sh',
                                     f'rereco_submission/{prepid}/{prepid}.sh')
            ssh_executor.execute_command([f'echo $HOSTNAME'])
            ssh_executor.execute_command([f'cd rereco_submission/{prepid}',
                                          f'chmod +x {prepid}.sh',
                                          f'export X509_USER_PROXY=$HOME/private/proxy.txt',
                                          f'./{prepid}.sh'])

            request.set('status', 'submitted')
            request_db.save(request.get_json())

        self.logger.info('Unlocked %s after submission', prepid)
