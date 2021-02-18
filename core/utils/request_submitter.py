"""
Module that has all classes used for request submission to computing
"""

import os
import time
from core_lib.utils.ssh_executor import SSHExecutor
from core_lib.utils.locker import Locker
from core_lib.database.database import Database
from core_lib.utils.connection_wrapper import ConnectionWrapper
from core_lib.utils.submitter import Submitter as BaseSubmitter
from core_lib.utils.common_utils import clean_split
from core_lib.utils.global_config import Config
from core.utils.emailer import Emailer


class RequestSubmitter(BaseSubmitter):
    """
    RequestSubmitter uploads scripts to submission machine, runs them to generate configs,
    uploads configs and job dict to ReqMgr2
    """

    def add(self, request, request_controller):
        """
        Add request to submission queue
        """
        prepid = request.get_prepid()
        super().add_task(prepid,
                         self.submit_request,
                         request=request,
                         controller=request_controller)

    def __handle_error(self, request, error_message):
        """
        Handle error that occured during submission, modify request accordingly
        """
        request_db = Database('requests')
        request.set('status', 'new')
        request.add_history('submission', 'failed', 'automatic')
        request_db.save(request.get_json())
        service_url = Config.get('service_url')
        emailer = Emailer()
        prepid = request.get_prepid()
        self.logger.warning('Submission of %s failed', prepid)
        subject = f'Request {prepid} submission failed'
        body = f'Hello,\n\nUnfortunately submission of {prepid} failed.\n'
        body += (f'You can find this request at '
                 f'{service_url}/requests?prepid={prepid}\n')
        body += f'Error message:\n\n{error_message}'
        recipients = emailer.get_recipients(request)
        emailer.send(subject, body, recipients)

    def __handle_success(self, request):
        """
        Handle notification of successful submission
        """
        prepid = request.get_prepid()
        last_workflow = request.get('workflows')[-1]['name']
        cmsweb_url = Config.get('cmsweb_url')
        self.logger.info('Submission of %s succeeded', prepid)
        service_url = Config.get('service_url')
        emailer = Emailer()
        subject = f'Request {prepid} submission succeeded'
        body = f'Hello,\n\nSubmission of {prepid} succeeded.\n'
        body += (f'You can find this request at '
                 f'{service_url}/requests?prepid={prepid}\n')
        body += f'Workflow in ReqMgr2 {cmsweb_url}/reqmgr2/fetch?rid={last_workflow}'
        recipients = emailer.get_recipients(request)
        emailer.send(subject, body, recipients)

    def __prepare_workspace(self, request, controller, ssh_executor, remote_directory):
        """
        Clean or create a remote directory and upload all needed files
        """
        prepid = request.get_prepid()
        self.logger.debug('Will prepare remote workspace for %s', prepid)
        ssh_executor.execute_command([f'rm -rf {remote_directory}',
                                      f'mkdir -p {remote_directory}'])
        with open(f'/tmp/{prepid}_generate.sh', 'w') as temp_file:
            config_file_content = controller.get_cmsdriver(request, for_submission=True)
            temp_file.write(config_file_content)

        with open(f'/tmp/{prepid}_upload.sh', 'w') as temp_file:
            upload_file_content = controller.get_config_upload_file(request, for_submission=True)
            temp_file.write(upload_file_content)

        # Upload config generation script - cmsDrivers
        ssh_executor.upload_file(f'/tmp/{prepid}_generate.sh',
                                 f'{remote_directory}/config_generate.sh')
        # Upload config upload to ReqMgr2 script
        ssh_executor.upload_file(f'/tmp/{prepid}_upload.sh',
                                 f'{remote_directory}/config_upload.sh')
        # Upload python script used by upload script
        ssh_executor.upload_file('./core_lib/utils/config_uploader.py',
                                 f'{remote_directory}/config_uploader.py')

        os.remove(f'/tmp/{prepid}_generate.sh')
        os.remove(f'/tmp/{prepid}_upload.sh')

    def __check_for_submission(self, request):
        """
        Perform one last check of values before submitting a request
        """
        prepid = request.get_prepid()
        self.logger.debug('Final check before submission for %s', prepid)
        if request.get('status') != 'submitting':
            raise Exception(f'Cannot submit a request with status {request.get("status")}')

        if not request.get('input')['dataset']:
            request_db = Database('requests')
            request.set('status', 'approved')
            request_db.save(request.get_json())
            raise Exception('Cannot submit a request without input dataset')

    def __generate_configs(self, request, ssh_executor, remote_directory):
        """
        SSH to a remote machine and generate cmsDriver config files
        """
        prepid = request.get_prepid()
        self.logger.debug('Will generate configs for %s', prepid)
        command = [f'cd {remote_directory}',
                   'chmod +x config_generate.sh',
                   'voms-proxy-init -voms cms --valid 4:00 --out $(pwd)/proxy.txt',
                   'export X509_USER_PROXY=$(pwd)/proxy.txt',
                   './config_generate.sh']
        stdout, stderr, exit_code = ssh_executor.execute_command(command)
        if exit_code != 0:
            raise Exception(f'Error generating configs for {prepid}.\n{stderr}')

        return stdout

    def __upload_configs(self, request, ssh_executor, remote_directory):
        """
        SSH to a remote machine and upload cmsDriver config files to ReqMgr2
        """
        prepid = request.get_prepid()
        self.logger.debug('Will upload configs for %s', prepid)
        command = [f'cd {remote_directory}',
                   'chmod +x config_upload.sh',
                   'export X509_USER_PROXY=$(pwd)/proxy.txt',
                   './config_upload.sh']
        stdout, stderr, exit_code = ssh_executor.execute_command(command)
        if exit_code != 0:
            raise Exception(f'Error uploading configs for {prepid}.\n{stderr}')

        stdout = [x for x in clean_split(stdout, '\n') if 'DocID' in x]
        # Get all lines that have DocID as tuples split by space
        stdout = [tuple(clean_split(x.strip(), ' ')[1:]) for x in stdout]
        return stdout

    def __update_sequences_with_config_hashes(self, request, config_hashes):
        """
        Iterate through request sequences and set config_id and harvesting_config_id values
        """
        for sequence in request.get('sequences'):
            sequence_config_names = sequence.get_config_file_names()
            sequence_name = sequence.get_name()
            if not sequence_config_names:
                continue

            # Make a copy of the list because items will be removed from original
            for hash_pair in list(config_hashes):
                config_name, config_hash = hash_pair
                if sequence_config_names['config'] == config_name:
                    sequence.set('config_id', config_hash)
                    config_hashes.remove(hash_pair)
                    self.logger.debug('Set %s %s for %s',
                                      config_name,
                                      config_hash,
                                      sequence_name)
                elif sequence_config_names.get('harvest') == config_name:
                    sequence.set('harvesting_config_id', config_hash)
                    config_hashes.remove(hash_pair)
                    self.logger.debug('Set %s %s for %s',
                                      config_name,
                                      config_hash,
                                      sequence_name)

        if config_hashes:
            raise Exception(f'Unused hashes: {config_hashes}')

        for sequence in request.get('sequences'):
            sequence_config_names = sequence.get_config_file_names()
            if not sequence_config_names:
                continue

            if not sequence.get('config_id'):
                sequence_name = sequence.get_name()
                raise Exception(f'Missing hash for {sequence_name}')

            if sequence.needs_harvesting() and not sequence.get('harvesting_config_id'):
                sequence_name = sequence.get_name()
                raise Exception(f'Missing harvesting hash for {sequence_name}')

    def submit_request(self, request, controller):
        """
        Method that is used by submission workers. This is where the actual submission happens
        """
        prepid = request.get_prepid()
        credentials_file = Config.get('credentials_file')
        remote_directory = Config.get('remote_path').rstrip('/')
        remote_directory = f'{remote_directory}/{prepid}'
        self.logger.debug('Will try to acquire lock for %s', prepid)
        with Locker().get_lock(prepid):
            self.logger.info('Locked %s for submission', prepid)
            request_db = Database('requests')
            request = controller.get(prepid)
            try:
                self.__check_for_submission(request)
                with SSHExecutor('lxplus.cern.ch', credentials_file) as ssh_executor:
                    # Start executing commands
                    self.__prepare_workspace(request, controller, ssh_executor, remote_directory)
                    # Create configs
                    self.__generate_configs(request, ssh_executor, remote_directory)
                    # Upload configs
                    config_hashes = self.__upload_configs(request, ssh_executor, remote_directory)
                    # Remove remote directory
                    ssh_executor.execute_command([f'rm -rf {remote_directory}'])

                self.logger.debug(config_hashes)
                # Iterate through uploaded configs and save their hashes in request sequences
                self.__update_sequences_with_config_hashes(request, config_hashes)
                # Submit job dict to ReqMgr2
                job_dict = controller.get_job_dict(request)
                cmsweb_url = Config.get('cmsweb_url')
                grid_cert = Config.get('grid_user_cert')
                grid_key = Config.get('grid_user_key')
                connection = ConnectionWrapper(host=cmsweb_url,
                                               cert_file=grid_cert,
                                               key_file=grid_key)
                workflow_name = self.submit_job_dict(job_dict, connection)
                # Update request after successful submission
                request.set('workflows', [{'name': workflow_name}])
                request.set('status', 'submitted')
                request.add_history('submission', 'succeeded', 'automatic')
                request_db.save(request.get_json())
                time.sleep(3)
                self.approve_workflow(workflow_name, connection)
                connection.close()
                controller.force_stats_to_refresh([workflow_name])
            except Exception as ex:
                self.__handle_error(request, str(ex))
                return

            self.__handle_success(request)

        controller.update_workflows(request)
        self.logger.info('Successfully finished %s submission', prepid)
