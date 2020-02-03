import logging
import time
from threading import Thread
from queue import Queue
from core.utils.ssh_executor import SSHExecutor
from core.utils.locker import Locker
from core.database.database import Database


class Worker(Thread):

    def __init__(self, name, task_queue):
        Thread.__init__(self)
        self.name = name
        self.queue = task_queue
        self.logger = logging.getLogger()
        self.logger.debug('Worker "%s" is being created', self.name)
        self.job_name = None
        self.jon_start_time = None
        self.start()

    def run(self):
        while True:
            self.logger.debug('Worker "%s" is waiting for tasks', self.name)
            func, job_name, args, kargs = self.queue.get()
            self.job_name = job_name
            self.job_start_time = time.time()
            self.logger.debug('Worker "%s" got a task. Queue size %s', self.name, self.queue.qsize())
            try:
                func(*args, **kargs)
            except Exception as e:
                self.logger.error(e)
            finally:
                self.logger.debug('Worker "%s" has finished a task. Queue size %s', self.name, self.queue.qsize())
                self.job_name = None
                self.job_start_time = 0


class WorkerPool:

    def __init__(self, workers_count, task_queue):
        self.logger = logging.getLogger()
        self.workers = []
        for i in range(workers_count):
            self.logger.info('Creating a worker')
            worker = Worker(f'worker-{i}', task_queue)
            self.workers.append(worker)

    def get_worker_status(self):
        status = {}
        now = time.time()
        for w in self.workers:
            status[w.name] = {'job_name': w.job_name,
                              'job_time': int(now - w.job_start_time if w.job_name else 0)}

        return status


class RequestSubmitter:

    # A FIFO queue. maxsize is an integer that sets the upperbound
    # limit on the number of items that can be placed in the queue.
    # If maxsize is less than or equal to zero, the queue size is infinite.
    __task_queue = Queue(maxsize=0)
    __worker_pool = WorkerPool(workers_count=2, task_queue=__task_queue)

    def __init__(self):
        self.logger = logging.getLogger()

    def add_request(self, request, controller):
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
        return RequestSubmitter.__task_queue.qsize()

    def get_worker_status(self):
        return RequestSubmitter.__worker_pool.get_worker_status()

    def submit_request(self, request, controller):
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
            with open(f'/tmp/{prepid}.sh', 'w') as f:
                f.write(controller.get_cmsdriver(request))

            ssh_executor.upload_file(f'/tmp/{prepid}.sh', f'rereco_submission/{prepid}/{prepid}.sh')
            ssh_executor.execute_command([f'echo $HOSTNAME'])
            ssh_executor.execute_command([f'cd rereco_submission/{prepid}',
                                          f'chmod +x {prepid}.sh',
                                          f'export X509_USER_PROXY=$HOME/private/proxy.txt',
                                          f'./{prepid}.sh'])

            request.set('status', 'submitted')
            request_db.save(request.get_json())

        self.logger.info('Unlocked %s after submission', prepid)
