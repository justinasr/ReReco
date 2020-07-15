"""
Module that has all classes used for request submission to computing
"""
import logging
import time
import json
import traceback
from threading import Thread
from queue import Queue, Empty
from core_lib.utils.ssh_executor import SSHExecutor
from core_lib.utils.locker import Locker
from core_lib.database.database import Database
from core_lib.utils.settings import Settings
from core_lib.utils.connection_wrapper import ConnectionWrapper
from core.utils.emailer import Emailer


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
                func, job_name, args, kargs = self.queue.get(timeout=1)
                self.job_name = job_name
                self.job_start_time = time.time()
                self.logger.debug('Worker "%s" got a task. Queue size %s',
                                  self.name,
                                  self.queue.qsize())
                try:
                    func(*args, **kargs)
                except Exception as ex:
                    self.logger.error(traceback.format_exc())
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
    __worker_pool = WorkerPool(workers_count=5, task_queue=__task_queue)

    def __init__(self):
        self.logger = logging.getLogger()

    def add_request(self, request, controller):
        """
        Add request to submission queue
        """
        prepid = request.get_prepid()
        for task in list(RequestSubmitter.__task_queue.queue):
            if task[1] == prepid:
                raise Exception(f'Task "{prepid}" is already in the queue')

        for worker, worker_info in RequestSubmitter.__worker_pool.get_worker_status().items():
            if worker_info['job_name'] == prepid:
                raise Exception(f'Task "{prepid}" is being worked on by "{worker}"')

        self.logger.info('Adding a task "%s". Queue size %s', prepid, self.get_queue_size())
        RequestSubmitter.__task_queue.put((self.submit_request, prepid, [request, controller], {}))

    def get_queue_size(self):
        """
        Return size of submission queue
        """
        return self.__task_queue.qsize()

    def get_worker_status(self):
        """
        Return dictionary of all worker statuses
        """
        return self.__worker_pool.get_worker_status()

    def get_names_in_queue(self):
        """
        Return a list of names that are waiting in the queue
        """
        return [x[1] for x in self.__task_queue.queue]

    def update_sequences_with_hashes(self, request, hashes):
        """
        Update request's sequences with given list of tupules with sequence names and hashes
        """

    def __handle_error(self, request, error_message):
        """
        Handle error that occured during submission, modify request accordingly
        """
        self.logger.error(error_message)
        request_db = Database('requests')
        request.set('status', 'new')
        request.add_history('submission', 'failed', 'automatic')
        request_db.save(request.get_json())
        service_url = Settings().get('service_url')
        emailer = Emailer()
        prepid = request.get_prepid()
        subject = f'Request {prepid} submission failed'
        body = f'Hello,\n\nUnfortunately submission of {prepid} failed.\n'
        body += (f'You can find this request at '
                 f'{service_url}/rereco/requests?prepid={prepid}\n')
        body += f'Error message:\n\n{error_message}'
        recipients = emailer.get_recipients(request)
        emailer.send(subject, body, recipients)

    def __handle_success(self, request):
        """
        Handle notification of successful submission
        """
        prepid = request.get_prepid()
        last_workflow = request.get('workflows')[-1]['name']
        cmsweb_url = Settings().get('cmsweb_url')
        self.logger.info('Submission of %s succeeded', prepid)
        service_url = Settings().get('service_url')
        emailer = Emailer()
        subject = f'Request {prepid} submission succeeded'
        body = f'Hello,\n\nSubmission of {prepid} succeeded.\n'
        body += (f'You can find this request at '
                 f'{service_url}/rereco/requests?prepid={prepid}\n')
        body += f'Workflow in ReqMgr2 {cmsweb_url}/reqmgr2/fetch?rid={last_workflow}'
        recipients = emailer.get_recipients(request)
        emailer.send(subject, body, recipients)

    def submit_request(self, request, controller):
        """
        Method that is used by submission workers. This is where the actual submission happens
        """
        credentials_path = Settings().get('credentials_path')
        ssh_executor = SSHExecutor('lxplus.cern.ch', credentials_path)
        prepid = request.get_prepid()
        with Locker().get_lock(prepid):
            request_db = Database('requests')
            request = controller.get(prepid)
            if request.get('status') != 'submitting':
                raise Exception(f'Cannot submit a request with status {request.get("status")}')

            if not request.get('input')['dataset']:
                request_db = Database('requests')
                request.set('status', 'approved')
                request_db.save(request.get_json())
                raise Exception(f'Cannot submit a request without input dataset')

            request.set('status', 'submitting')
            request_db.save(request.get_json())
            request = controller.get(prepid)
            self.logger.info('Locked %s for submission', prepid)
            ssh_executor.execute_command([f'rm -rf rereco_submission/{prepid}',
                                          f'mkdir -p rereco_submission/{prepid}'])
            with open(f'/tmp/{prepid}.sh', 'w') as temp_file:
                config_file_content = controller.get_cmsdriver(request, for_submission=True)
                temp_file.write(config_file_content)

            with open(f'/tmp/{prepid}_upload.sh', 'w') as temp_file:
                upload_file_content = controller.get_config_upload_file(request)
                temp_file.write(upload_file_content)

            # Upload config generation script - cmsDrivers
            ssh_executor.upload_file(f'/tmp/{prepid}.sh',
                                     f'rereco_submission/{prepid}/{prepid}.sh')
            # Upload config upload to ReqMgr2 script
            ssh_executor.upload_file(f'/tmp/{prepid}_upload.sh',
                                     f'rereco_submission/{prepid}/{prepid}_upload.sh')
            # Upload python script used by upload script
            ssh_executor.upload_file(f'./core_lib/utils/config_uploader.py',
                                     f'rereco_submission/{prepid}/config_uploader.py')
            # Start executing commands
            # Create configs
            config_gen_command = [f'cd rereco_submission/{prepid}',
                                  f'chmod +x {prepid}.sh',
                                  f'voms-proxy-init -voms cms --valid 4:00',
                                  f'export X509_USER_PROXY=$(voms-proxy-info --path)',
                                  f'./{prepid}.sh']
            config_get_output = ssh_executor.execute_command(config_gen_command)
            _, config_gen_stderr, config_gen_exit_code = config_get_output
            if config_gen_exit_code != 0:
                self.__handle_error(request,
                                    f'Error generating configs for {prepid}.\n{config_gen_stderr}')
                return

            # Upload configs
            config_upload_command = [f'cd rereco_submission/{prepid}',
                                     f'chmod +x {prepid}_upload.sh',
                                     f'./{prepid}_upload.sh']
            config_upload_output = ssh_executor.execute_command(config_upload_command)
            upload_stdout, upload_stderr, upload_exit_code = config_upload_output
            if upload_exit_code:
                self.__handle_error(request,
                                    f'Error uploading configs for {prepid}.\n{upload_stderr}')
                return

            upload_stdout = upload_stdout.split('\n')
            # Get all lines that have DocID as tuples split by space
            upload_stdout = [tuple(x.strip() for x in x.split(' ') if x.strip())
                             for x in upload_stdout if 'DocID' in x]
            expected_config_file_names = request.get_config_file_names()
            for docid, config_name, config_hash in upload_stdout:
                if docid != 'DocID':
                    self.__handle_error(request,
                                        f'Output is different than expected for {prepid}: '
                                        f'{docid} {config_name} {config_hash}')
                    return

                for sequence_index, sequence_configs in enumerate(expected_config_file_names):
                    if sequence_configs['config'] == config_name:
                        self.logger.debug('Set hash %s as config id for sequence %s',
                                          config_hash,
                                          sequence_index)
                        request.get('sequences')[sequence_index].set('config_id',
                                                                     config_hash)
                        sequence_configs['config'] = None
                        break
                    elif sequence_configs.get('harvest') == config_name:
                        self.logger.debug('Set hash %s as harvesting config id for sequence %s',
                                          config_hash,
                                          sequence_index)
                        request.get('sequences')[sequence_index].set('harvesting_config_id',
                                                                     config_hash)
                        sequence_configs['harvest'] = None
                        break
                else:
                    self.__handle_error(request,
                                        f'Unexpected DocID for {prepid}: {config_name} '
                                        f'{config_name} {config_hash}')
                    return

            for sequence_configs in expected_config_file_names:
                if sequence_configs['config'] is not None:
                    self.__handle_error(request,
                                        f'Missing DocID: {sequence_configs["config"]}')
                    return

                if sequence_configs.get('harvest') is not None:
                    self.__handle_error(request,
                                        f'Missing DocID: {sequence_configs["harvest"]}')
                    return

            try:
                job_dict = controller.get_job_dict(request)
            except Exception as ex:
                self.__handle_error(request,
                                    f'Error getting {prepid} job dict:\n{str(ex)}')
                return

            headers = {'Content-type': 'application/json',
                       'Accept': 'application/json'}

            cmsweb_url = Settings().get('cmsweb_url')
            connection = ConnectionWrapper(host=cmsweb_url, keep_open=True)
            try:
                # Submit job dictionary (ReqMgr2 JSON)
                reqmgr_response = connection.api('POST',
                                                 '/reqmgr2/data/request',
                                                 job_dict,
                                                 headers)
                self.logger.info(reqmgr_response)
                workflow_name = json.loads(reqmgr_response).get('result', [])[0].get('request')
                request.set('workflows', [{'name': workflow_name}])
                request.set('status', 'submitted')
                request.add_history('submission', 'succeeded', 'automatic')
                request_db.save(request.get_json())
            except Exception:
                self.__handle_error(request,
                                    f'Error submitting {prepid} to ReqMgr2:\n{reqmgr_response}')
                return

            try:
                # Try to approve workflow (move to assignment-approved) after few seconds
                time.sleep(3)
                approve_response = connection.api('PUT',
                                                  f'/reqmgr2/data/request/{workflow_name}',
                                                  {'RequestStatus': 'assignment-approved'},
                                                  headers)
            except Exception as ex:
                self.logger.error('Error approving %s: %s', prepid, str(ex))

            connection.close()
            self.logger.info(approve_response)
            controller.force_stats_to_refresh([workflow_name])
            self.__handle_success(request)

        controller.update_workflows(request)
        self.logger.info('Successfully finished %s submission', prepid)
