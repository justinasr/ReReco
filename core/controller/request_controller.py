"""
Module that contains RequestController class
"""
import json
import environment
from core_lib.database.database import Database
from core_lib.utils.common_utils import (change_workflow_priority,
                                         cmsweb_reject_workflows,
                                         dbs_dataset_runs,
                                         get_scram_arch,
                                         config_cache_lite_setup,
                                         dbs_datasetlist,
                                         get_workflows_from_stats,
                                         get_workflows_from_stats_for_prepid,
                                         refresh_workflows_in_stats, run_commands_in_cmsenv)
from core_lib.utils.settings import Settings
from core_lib.controller.controller_base import ControllerBase
from core.model.request import Request
from core.model.subcampaign import Subcampaign
from core.model.ticket import Ticket
from core.utils.request_submitter import RequestSubmitter
from core.controller.subcampaign_controller import SubcampaignController


DEAD_WORKFLOW_STATUS = {'rejected', 'aborted', 'failed', 'rejected-archived',
                        'aborted-archived', 'failed-archived', 'aborted-completed'}


class RequestController(ControllerBase):
    """
    Controller that has all actions related to a request
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'requests'
        self.model_class = Request

    def create(self, json_data):
        # Get a subcampaign
        subcampaign_db = Database('subcampaigns')
        subcampaign_name = json_data.get('subcampaign')
        subcampaign_json = subcampaign_db.get(subcampaign_name)
        if not subcampaign_json:
            raise ValueError(f'Subcampaign "{subcampaign_name}" does not exist')

        request_db = Database(self.database_name)
        subcampaign = Subcampaign(json_input=subcampaign_json)

        json_data['cmssw_release'] = subcampaign.get('cmssw_release')
        json_data['subcampaign'] = subcampaign.get_prepid()
        json_data['prepid'] = 'PlaceholderPrepID'
        new_request = Request(json_input=json_data)
        if not json_data.get('sequences'):
            new_request.set('sequences', subcampaign.get('sequences'))

        for sequence in new_request.get('sequences'):
            sequence.set('config_id', '')
            sequence.set('harvesting_config_id', '')

        if not json_data.get('time_per_event'):
            new_request.set('time_per_event', [1.0] * len(subcampaign.get('sequences')))

        if not json_data.get('size_per_event'):
            new_request.set('size_per_event', [1.0] * len(subcampaign.get('sequences')))

        if not json_data.get('memory'):
            new_request.set('memory', subcampaign.get('memory'))

        if not json_data.get('energy'):
            new_request.set('energy', subcampaign.get('energy'))

        if json_data.get('enable_harvesting') is None:
            json_data['enable_harvesting'] = subcampaign.get('enable_harvesting')

        request_input = new_request.get('input')
        input_dataset = request_input.get('dataset')
        input_request_prepid = request_input.get('request')
        # Prepid is made of era, dataset and processing string
        # Either they are taken from input dataset or input request
        # Only one must be provided
        self.logger.info('Input of request is %s', request_input)
        if input_dataset and input_request_prepid:
            raise AssertionError('Request cannot have both input request and input dataset')

        if input_dataset and not input_request_prepid:
            input_dataset_parts = [x for x in input_dataset.split('/') if x]
            era = input_dataset_parts[1].split('-')[0]
            dataset = input_dataset_parts[0]
        elif not input_dataset and input_request_prepid:
            input_request_json = request_db.get(input_request_prepid)
            if not input_request_json:
                raise ValueError(f'Request "{input_request_prepid}" does not exist')

            input_request = Request(json_input=input_request_json)
            era = input_request.get_era()
            dataset = input_request.get_dataset()
        else:
            raise AssertionError('Request must have either a input request or input dataset')

        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{dataset}-{processing_string}'
        with self.locker.get_lock(f'create-request-prepid-{prepid_middle_part}'):
            # Get a new serial number
            serial_number = self.get_highest_serial_number(request_db,
                                                           f'ReReco-{prepid_middle_part}-*')
            serial_number += 1
            prepid = f'ReReco-{prepid_middle_part}-{serial_number:05d}'
            new_request.set('prepid', prepid)
            new_request_json = super().create(new_request.get_json())

        return new_request_json

    def check_for_create(self, obj):
        sequences = obj.get('sequences')
        size_per_event = obj.get('size_per_event')
        time_per_event = obj.get('time_per_event')
        if len(sequences) != len(size_per_event):
            raise ValueError(f'Expected {len(sequences)} size per event '
                             f'values, found {len(size_per_event)}')

        if len(sequences) != len(time_per_event):
            raise ValueError(f'Expected {len(sequences)} time per event '
                             f'values, found {len(time_per_event)}')

        return super().check_for_create(obj)

    def check_for_update(self, old_obj, new_obj, changed_values):
        if old_obj.get('status') == 'submitting':
            raise AssertionError((
                'You are now allowed to update request '
                'while it is being submitted'
            ))

        sequences = new_obj.get('sequences')
        size_per_event = new_obj.get('size_per_event')
        time_per_event = new_obj.get('time_per_event')
        if len(sequences) != len(size_per_event):
            raise ValueError(f'Expected {len(sequences)} size per event '
                            f'values, found {len(size_per_event)}')

        if len(sequences) != len(time_per_event):
            raise ValueError(f'Expected {len(sequences)} time per event '
                            f'values, found {len(time_per_event)}')

        return super().check_for_update(old_obj, new_obj, changed_values)

    def check_for_delete(self, obj):
        if obj.get('status') != 'new':
            raise AssertionError('Request must be in status "new" before it is deleted')

        requests_db = Database('requests')
        prepid = obj.get_prepid()
        subsequent_requests_query = f'input.request={prepid}'
        subsequent_requests = requests_db.query(subsequent_requests_query)
        if subsequent_requests:
            subsequent_requests_prepids = ', '.join([r['prepid'] for r in subsequent_requests])
            raise AssertionError(f'Request cannot be deleted because it is input request'
                                 f'for {subsequent_requests_prepids}. Delete these requests first')

        return True

    def after_update(self, old_obj, new_obj, changed_values):
        if new_obj.get('status') == 'submitted':
            if old_obj.get('priority') != new_obj.get('priority'):
                self.change_request_priority(new_obj, new_obj.get('priority'))

        if new_obj.get('runs') != old_obj.get('runs'):
            self.update_subsequent_requests(new_obj, {'runs': new_obj.get('runs')})

    def after_delete(self, obj):
        prepid = obj.get_prepid()
        tickets_db = Database('tickets')
        tickets = tickets_db.query(f'created_requests={prepid}')
        self.logger.debug(json.dumps(tickets, indent=2))
        for ticket_json in tickets:
            ticket_prepid = ticket_json['prepid']
            with self.locker.get_lock(ticket_prepid):
                ticket_json = tickets_db.get(ticket_prepid)
                ticket = Ticket(json_input=ticket_json)
                created_requests = ticket.get('created_requests')
                if prepid in created_requests:
                    created_requests.remove(prepid)

                ticket.set('created_requests', created_requests)
                ticket.add_history('remove_request', prepid, None)
                tickets_db.save(ticket.get_json())

        return True

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        creating_new = not bool(prepid)
        status_new = obj.get('status') == 'new'
        editing_info['notes'] = True
        editing_info['energy'] = True
        editing_info['priority'] = obj.get('status') != 'done'
        editing_info['subcampaign'] = creating_new
        editing_info['processing_string'] = creating_new
        editing_info['sequences'] = status_new
        editing_info['lumisections'] = status_new
        editing_info['memory'] = status_new
        editing_info['input'] = creating_new
        editing_info['runs'] = status_new
        editing_info['time_per_event'] = status_new
        editing_info['size_per_event'] = status_new
        editing_info['cmssw_release'] = status_new
        editing_info['enable_harvesting'] = status_new
        editing_info['job_dict_overwrite'] = status_new

        return editing_info

    def get_cmsdriver(self, request, for_submission=False):
        """
        Get bash script with cmsDriver commands for a given request
        If script will be used for submission, replace input file with placeholder
        """
        self.logger.debug('Getting cmsDriver commands for %s', request.get_prepid())
        bash = ['#!/bin/bash',
                '']

        if for_submission:
            drivers = request.get_cmsdrivers('_placeholder_.root')
        else:
            drivers = request.get_cmsdrivers()

        cmssw_release = request.get('cmssw_release')
        scram_arch = get_scram_arch(cmssw_release)
        bash += run_commands_in_cmsenv(drivers, cmssw_release, scram_arch).split('\n')
        return '\n'.join(bash)

    def get_config_upload_file(self, request):
        """
        Get bash script that would upload config files to ReqMgr2
        """
        self.logger.debug('Getting config upload script for %s', request.get_prepid())
        database_url = environment.CMSWEB_URL.replace('https://', '').replace('http://', '')
        bash = ['#!/bin/bash',
                '']
        config_names = []
        for configs in request.get_config_file_names():
            config_names.append(configs['config'])
            if configs.get('harvest'):
                config_names.append(configs['harvest'])


        # Check if all expected config files are present
        for config_name in config_names:
            bash += [f'if [ ! -s "{config_name}.py" ]; then',
                     f'  echo "File {config_name}.py is missing" >&2',
                     '  exit 1',
                     'fi',
                     '']

        # Use ConfigCacheLite and TweakMakerLite instead of WMCore
        bash += config_cache_lite_setup().split('\n')
        bash += ['']

        commands = []
        for config_name in config_names:
            # Run config uploader
            commands.append(('$PYTHON_INT config_uploader.py '
                             f'--file $(pwd)/{config_name}.py '
                             f'--label {config_name} '
                             '--group ppd '
                             '--user $(echo $USER) '
                             f'--db {database_url} || exit $?'))

        if commands:
            cmssw_release = request.get('cmssw_release')
            scram_arch = get_scram_arch(cmssw_release)
            bash += run_commands_in_cmsenv(commands, cmssw_release, scram_arch).split('\n')

        return '\n'.join(bash)

    def get_job_dict(self, request):
        """
        Return a dictionary for ReqMgr2
        """
        prepid = request.get_prepid()
        self.logger.debug('Getting job dict for %s', prepid)
        sequences = request.get('sequences')
        database_url = environment.CMSWEB_URL + '/couchdb'
        request_string = request.get_request_string()
        campaign_name = request.get('subcampaign').split('-')[0]
        job_dict = {}
        job_dict['Campaign'] = campaign_name
        job_dict['CMSSWVersion'] = request.get('cmssw_release')
        job_dict['ConfigCacheUrl'] = database_url
        job_dict['CouchURL'] = database_url
        job_dict['EnableHarvesting'] = False
        job_dict['Group'] = 'PPD'
        job_dict['Memory'] = request.get('memory')
        job_dict['RequestType'] = 'ReReco'
        job_dict['PrepID'] = request.get_prepid()
        job_dict['Requestor'] = 'pdmvserv'
        job_dict['RequestPriority'] = request.get('priority')
        job_dict['RequestString'] = request_string
        job_dict['ScramArch'] = get_scram_arch(request.get('cmssw_release'))
        job_dict['SizePerEvent'] = request.get('size_per_event')[0]
        job_dict['TimePerEvent'] = request.get('time_per_event')[0]
        if len(sequences) <= 1:
            job_dict.update(self.get_job_dict_singletask(request, sequences))
        else:
            job_dict.update(self.get_job_dict_taskchain(request, sequences))

        if job_dict.get('EnableHarvesting'):
            if not environment.DEVELOPMENT:
                # Do not upload to prod DQM GUI in dev
                job_dict['DQMUploadUrl'] = 'https://cmsweb.cern.ch/dqm/offline'
            else:
                # Upload to some dev DQM GUI
                job_dict['DQMUploadUrl'] = 'https://cmsweb-testbed.cern.ch/dqm/dev'

        job_dict_overwrite = request.get('job_dict_overwrite')
        if job_dict_overwrite:
            self.logger.info('Overwriting job dict for %s with %s', prepid, job_dict_overwrite)
            self.apply_job_dict_overwrite(job_dict, job_dict_overwrite)

        return job_dict

    def apply_job_dict_overwrite(self, job_dict, overwrite):
        """
        Apply overwrites to job dictionary
        """
        for key, value in overwrite.items():
            obj = job_dict
            key_parts = key.split('.')
            for part in key_parts[:-1]:
                if part in obj:
                    obj = obj[part]
                else:
                    break
            else:
                obj[key_parts[-1]] = value

    def get_job_dict_taskchain(self, request, sequences):
        """
        Return a dictionary with information needed for the TaskChain submission
        This does not return a full Job Dict, but only the attributes specific for TaskChain
        """
        input_dataset = request.get('input')['dataset']
        acquisition_era = request.get_era()
        processing_string = request.get('processing_string')
        campaign_name = request.get('subcampaign').split('-')[0]
        memory = request.get('memory')
        size_per_event = request.get('size_per_event')
        time_per_event = request.get('time_per_event')
        job_dict = {}
        for index, sequence in enumerate(sequences):
            task_dict = {}
            task_dict['AcquisitionEra'] = acquisition_era
            task_dict['ProcessingString'] = processing_string
            task_dict['Campaign'] = campaign_name
            task_dict['Memory'] = memory
            task_dict['TaskName'] = f'Task{index + 1}'
            task_dict['GlobalTag'] = sequence.get('conditions')
            task_dict['Multicore'] = sequence.get('nThreads')
            task_dict['TimePerEvent'] = time_per_event[index]
            task_dict['SizePerEvent'] = size_per_event[index]
            task_dict['KeepOutput'] = True
            if index == 0:
                lumisections = request.get('lumisections')
                runs = request.get('runs')
                if lumisections:
                    task_dict['LumiList'] = lumisections
                elif runs:
                    task_dict['RunWhitelist'] = runs

                if input_dataset:
                    task_dict['InputDataset'] = input_dataset
            else:
                task_dict['InputFromOutputModule'] = sequences[index-1].get_output_module()
                task_dict['InputTask'] = f'Task{index}'

            if sequence.get('config_id'):
                task_dict['ConfigCacheID'] = sequence.get('config_id')

            if sequence.needs_harvesting():
                job_dict['EnableHarvesting'] = True
                if sequence.get('harvesting_config_id'):
                    job_dict['DQMConfigCacheID'] = sequence.get('harvesting_config_id')

            if sequence.get_gpu_requires() != 'forbidden':
                task_dict['GPUParams'] = json.dumps(sequence.get_gpu_dict(), sort_keys=True)
                task_dict['RequiresGPU'] = sequence.get_gpu_requires()

            job_dict[f'Task{index + 1}'] = task_dict

        job_dict['TaskChain'] = len(sequences)
        job_dict['RequestType'] = 'TaskChain'
        job_dict['AcquisitionEra'] = job_dict['Task1']['AcquisitionEra']
        job_dict['ProcessingString'] = job_dict['Task1']['ProcessingString']
        job_dict['GlobalTag'] = job_dict['Task1']['GlobalTag']
        self.logger.debug('Returning %s TaskChain dict: %s', request.get_prepid(), job_dict)
        return job_dict

    def get_job_dict_singletask(self, request, sequences):
        """
        Return a dictionary with information needed for the old style workflow submission
        This does not return a full Job Dict, but only the attributes specific for it
        """
        sequence = sequences[0]
        input_dataset = request.get('input')['dataset']
        acquisition_era = request.get_era()
        processing_string = request.get('processing_string')
        job_dict = {}
        job_dict['AcquisitionEra'] = acquisition_era
        job_dict['ProcessingString'] = processing_string
        job_dict['GlobalTag'] = sequence.get('conditions')
        job_dict['Multicore'] = sequence.get('nThreads')
        job_dict['Scenario'] = sequence.get('scenario')
        lumisections = request.get('lumisections')
        runs = request.get('runs')
        if lumisections:
            job_dict['LumiList'] = lumisections
        elif runs:
            job_dict['RunWhitelist'] = runs

        if input_dataset:
            job_dict['InputDataset'] = input_dataset

        if sequence.get('config_id'):
            job_dict['ConfigCacheID'] = sequence.get('config_id')

        if sequence.needs_harvesting():
            job_dict['EnableHarvesting'] = True
            if sequence.get('harvesting_config_id'):
                job_dict['DQMConfigCacheID'] = sequence.get('harvesting_config_id')

        if sequence.get_gpu_requires() != 'forbidden':
            job_dict['GPUParams'] = json.dumps(sequence.get_gpu_dict(), sort_keys=True)
            job_dict['RequiresGPU'] = sequence.get_gpu_requires()

        self.logger.debug('Returning %s single task dict: %s', request.get_prepid(), job_dict)
        return job_dict

    def update_input_dataset(self, request):
        """
        Update input dataset name from input request (if exists)
        Update runs from input request if they are not specified yet
        Input dataset is datatier aware, so if input request produced
        AOD + MiniAOD and this request is reMini, it should select AOD of input
        request and not MiniAOD
        """
        prepid = request.get_prepid()
        input_request_prepid = request.get('input')['request']
        if input_request_prepid:
            input_request = self.get(input_request_prepid)
            output_datasets = input_request.get('output_datasets')
            new_input_dataset = self.pick_input_dataset(request, input_request)
            should_update = False
            if output_datasets and new_input_dataset:
                request.get('input')['dataset'] = new_input_dataset
                should_update = True
            elif not output_datasets:
                request.get('input')['dataset'] = ''
                should_update = True

            if should_update:
                self.update(request.get_json(), force_update=True)
        else:
            self.logger.info('Did not update %s input dataset', prepid)

    def pick_input_dataset(self, request, input_request):
        """
        Pick input dataset from the given input request using datatier mapping
        or default to the last output dataset of input request
        """
        settings = Settings()
        datatiers = request.get_datatiers()
        datasets = input_request.get('output_datasets')
        if datatiers:
            datatier = datatiers[0]
            mapping = settings.get('datatier_mapping', {})
            self.logger.debug('Request %s datatier is %s mapping %s',
                              request.get_prepid(),
                              datatier,
                              mapping)
            input_datatiers = mapping.get(datatier, [])
            for input_datatier in input_datatiers:
                for dataset in datasets:
                    if dataset.endswith(f'/{input_datatier}'):
                        return dataset

            self.logger.warning('Could not find input dataset for %s in %s',
                                request.get_prepid(),
                                input_request.get_prepid())

        if datasets:
            return datasets[-1]

        return ''


    def update_status(self, request, status, timestamp=None):
        """
        Set new status to request, update history accordingly and save to database
        """
        request_db = Database(self.database_name)
        request.set('status', status)
        request.add_history('status', status, None, timestamp)
        request_db.save(request.get_json())

    def next_status(self, request):
        """
        Trigger request to move to next status
        """
        prepid = request.get_prepid()
        with self.locker.get_nonblocking_lock(prepid):
            if request.get('status') == 'new':
                self.move_request_to_approved(request)
            elif request.get('status') == 'approved':
                self.move_request_to_submitting(request)
            elif request.get('status') == 'submitting':
                raise AssertionError('Request is being submitted')
            elif request.get('status') == 'submitted':
                self.move_request_to_done(request)
            elif request.get('status') == 'done':
                raise AssertionError('Request is already done')

        return request

    def previous_status(self, request):
        """
        Trigger request to move to previous status
        """
        prepid = request.get_prepid()
        with self.locker.get_nonblocking_lock(prepid):
            if request.get('status') == 'approved':
                self.move_request_back_to_new(request)
            elif request.get('status') == 'submitting':
                self.move_request_back_to_approved(request)
            elif request.get('status') == 'submitted':
                self.move_request_back_to_approved(request)
            elif request.get('status') == 'done':
                self.move_request_back_to_approved(request)
                self.move_request_back_to_new(request)

        return request

    def move_request_to_approved(self, request):
        """
        Try to move rquest to approved
        """
        self.update_input_dataset(request)
        self.update_status(request, 'approved')
        return request

    def move_request_to_submitting(self, request):
        """
        Try to move request to submitting status and get sumbitted
        """
        self.update_input_dataset(request)
        input_dataset = request.get('input')['dataset']
        if not input_dataset.strip():
            prepid = request.get_prepid()
            raise AssertionError(f'Could not move {prepid} to submitting '
                                 'because it does not have input dataset')

        input_request_prepid = request.get('input')['request']
        if input_request_prepid:
            input_request = self.get(input_request_prepid)
            input_request_status = input_request.get('status')
            if input_request_status != 'done':
                raise AssertionError(f'Input request {input_request_prepid} status is '
                                     f'"{input_request_status}", not "done"')

        input_dataset_info = dbs_datasetlist([input_dataset])
        if not input_dataset_info:
            raise RuntimeError(f'Could not get info about input dataset "{input_dataset}"')

        dataset_access_type = input_dataset_info[0].get('dataset_access_type', 'unknown')
        self.logger.info('%s access type is %s', input_dataset, dataset_access_type)
        if dataset_access_type != 'VALID':
            raise AssertionError(f'{input_dataset} type is {dataset_access_type}, it must be VALID')

        RequestSubmitter().add(request, self)
        self.update_status(request, 'submitting')
        return request

    def move_request_to_done(self, request):
        """
        Try to move request to done status
        """
        prepid = request.get_prepid()
        request = self.update_workflows(request)
        workflows = request.get('workflows')
        workflows = [w for w in workflows if w['type'].lower() != 'resubmission']
        if workflows:
            last_workflow = workflows[-1]
            for output_dataset in last_workflow['output_datasets']:
                dataset_type = output_dataset['type']
                if dataset_type.lower() != 'valid':
                    dataset_name = output_dataset['name']
                    raise AssertionError(f'Could not move {prepid} to "done" '
                                         f'because {dataset_name} is {dataset_type}')

            for status in last_workflow['status_history']:
                if status['status'].lower() in ('announced', 'normal-archived'):
                    completed_timestamp = status['time']
                    break
            else:
                last_workflow_name = last_workflow['name']
                raise AssertionError(
                    (
                        f'Could not move {prepid} to "done" because {last_workflow_name} '
                        'is not yet "announced" or "normal-archived"'
                    )
                )

            self.update_status(request, 'done', completed_timestamp)
            # Submit all subsequent requests
            self.submit_subsequent_requests(request)
        else:
            raise AssertionError(f'{prepid} does not have any workflows in computing')

        return request

    def submit_subsequent_requests(self, request):
        """
        Submit all requests that have given request as input
        """
        request_db = Database('requests')
        prepid = request.get_prepid()
        query = f'input.request={prepid}&&status=approved'
        subsequent_requests = request_db.query(query)
        self.logger.info('Found %s subsequent requests for %s: %s',
                         len(subsequent_requests),
                         prepid,
                         [r['prepid'] for r in subsequent_requests])
        for subsequent_request_json in subsequent_requests:
            subsequent_request_prepid = subsequent_request_json.get('prepid', '')
            try:
                subsequent_request = self.get(subsequent_request_prepid)
                self.update_input_dataset(subsequent_request)
                self.next_status(subsequent_request)
            except Exception as ex:
                self.logger.error('Error moving %s to next status: %s',
                                  subsequent_request_prepid,
                                  ex)

    def update_subsequent_requests(self, request, values):
        """
        Update all subsequent requests
        """
        request_db = Database('requests')
        prepid = request.get_prepid()
        query = f'input.request={prepid}'
        requests = request_db.query(query)
        self.logger.info('Found %s subsequent requests for %s: %s',
                         len(requests),
                         prepid,
                         [r['prepid'] for r in requests])
        for request_json in requests:
            if request_json.get('status') not in ('new', 'approved'):
                continue

            request_prepid = request_json.get('prepid', '')
            try:
                subsequent_request = self.get(request_prepid)
                for key, value in values.items():
                    subsequent_request.set(key, value)

                self.update(subsequent_request.get_json())
            except Exception as ex:
                self.logger.error('Error updating subsequent request %s: %s',
                                  request_prepid,
                                  ex)

    def move_request_back_to_new(self, request):
        """
        Try to move rquest back to new
        """
        request_input = request.get('input')
        input_dataset = request_input.get('dataset')
        input_request_prepid = request_input.get('request')
        # If request has both input request and input dataset set, set input
        # dataset value to empty string
        if input_dataset and input_request_prepid:
            request_input['dataset'] = ''

        self.update_status(request, 'new')
        return request

    def move_request_back_to_approved(self, request):
        """
        Try to move rquest back to approved
        """
        active_workflows = self.pick_active_workflows(request)
        refresh_workflows_in_stats([w['name'] for w in active_workflows])
        # Take active workflows again in case any of them changed during Stats refresh
        active_workflows = self.pick_active_workflows(request)
        if active_workflows:
            self.reject_workflows(active_workflows)

        request.set('workflows', [])
        request.set('total_events', 0)
        request.set('completed_events', 0)
        for sequence in request.get('sequences'):
            sequence.set('config_id', '')
            sequence.set('harvesting_config_id', '')

        request.set('output_datasets', [])
        self.update_status(request, 'approved')
        return request

    def get_dataset_runs(self, dataset):
        """
        Fetch a list of runs from DBS for a given dataset
        """
        runs = dbs_dataset_runs(dataset)
        self.logger.debug('Fetched %s runs for %s from DBS', len(runs), dataset)
        return runs

    def get_lumisections(self, subcampaign_name, runs):
        """
        Get lumisection ranges in a subcampaign's dcs json for given runs
        """
        subcampaign_controller = SubcampaignController()
        dcs_json = subcampaign_controller.get_dcs_json(subcampaign_name)
        runs = {str(r) for r in runs}
        lumisections = {run: lumis for run, lumis in dcs_json.items() if run in runs}
        self.logger.debug('Fetched %s runs with lumi ranges for %s and %s runs',
                          len(lumisections),
                          subcampaign_name,
                          len(runs))
        return lumisections

    def get_runs(self, subcampaign_name, input_dataset):
        """
        Return a list of runs for given input dataset in a subcampaign
        """
        subcampaign_controller = SubcampaignController()
        dbs_runs = set(self.get_dataset_runs(input_dataset))
        dcs_json = subcampaign_controller.get_dcs_json(subcampaign_name)
        dcs_runs = set(int(x) for x in list(dcs_json.keys()))
        if dbs_runs and dcs_runs:
            all_runs = sorted(list(dbs_runs & dcs_runs))
        else:
            all_runs = sorted(list(dbs_runs | dcs_runs))

        self.logger.info('Got %s runs from DBS and %s runs from DCS for %s, total is %s runs',
                         len(dbs_runs),
                         len(dcs_runs),
                         input_dataset,
                         len(all_runs))

        return all_runs

    def get_runs_for_request(self, request):
        """
        Return a list of runs for given request
        """
        subcampaign_name = request.get('subcampaign')
        input_dataset = request.get('input')['dataset']
        return self.get_runs(subcampaign_name, input_dataset)

    def get_lumisections_for_request(self, request, runs=None):
        """
        Return a dictionary of runs and lumisection ranges
        If no runs are provided, request's runs will be used
        """
        subcampaign_name = request.get('subcampaign')
        if runs:
            return self.get_lumisections(subcampaign_name, runs)

        return self.get_lumisections(subcampaign_name, request.get('runs'))

    def pick_workflows(self, all_workflows, output_datasets):
        """
        Pick, process and sort workflows from computing based on output datasets
        """
        new_workflows = []
        self.logger.info('Picking workflows %s for datasets %s',
                         [x['RequestName'] for x in all_workflows.values()],
                         output_datasets)
        for _, workflow in all_workflows.items():
            new_workflow = {'name': workflow['RequestName'],
                            'type': workflow['RequestType'],
                            'output_datasets': [],
                            'status_history': []}
            for output_dataset in output_datasets:
                for history_entry in reversed(workflow.get('EventNumberHistory', [])):
                    if output_dataset in history_entry['Datasets']:
                        dataset_dict = history_entry['Datasets'][output_dataset]
                        new_workflow['output_datasets'].append({'name': output_dataset,
                                                                'type': dataset_dict['Type'],
                                                                'events': dataset_dict['Events']})
                        break

            for request_transition in workflow.get('RequestTransition', []):
                new_workflow['status_history'].append({'time': request_transition['UpdateTime'],
                                                       'status': request_transition['Status']})

            new_workflows.append(new_workflow)

        new_workflows = sorted(new_workflows, key=lambda w: '_'.join(w['name'].split('_')[-3:]))
        self.logger.info('Picked workflows:\n%s',
                         ', '.join([w['name'] for w in new_workflows]))
        return new_workflows

    def get_output_datasets(self, request, all_workflows):
        """
        Return a list of sorted output datasets for request from given workflows
        """
        output_datatiers = []
        prepid = request.get_prepid()
        for sequence in request.get('sequences'):
            output_datatiers.extend(sequence.get('datatier'))

        output_datatiers_set = set(output_datatiers)
        self.logger.info('%s output datatiers are: %s', prepid, ', '.join(output_datatiers))
        output_datasets_tree = {k: {} for k in output_datatiers}
        for workflow_name, workflow in all_workflows.items():
            if workflow.get('RequestType', '').lower() == 'resubmission':
                continue

            status_history = set(x['Status'] for x in workflow.get('RequestTransition', []))
            if DEAD_WORKFLOW_STATUS & status_history:
                self.logger.debug('Ignoring %s', workflow_name)
                continue

            for output_dataset in workflow.get('OutputDatasets', []):
                output_dataset_parts = [x.strip() for x in output_dataset.split('/')]
                output_dataset_datatier = output_dataset_parts[-1]
                output_dataset_no_datatier = '/'.join(output_dataset_parts[:-1])
                output_dataset_no_version = '-'.join(output_dataset_no_datatier.split('-')[:-1])
                if output_dataset_datatier in output_datatiers_set:
                    datatier_tree = output_datasets_tree[output_dataset_datatier]
                    if output_dataset_no_version not in datatier_tree:
                        datatier_tree[output_dataset_no_version] = []

                    datatier_tree[output_dataset_no_version].append(output_dataset)

        self.logger.debug('Output datasets tree:\n%s',
                          json.dumps(output_datasets_tree,
                                     indent=2,
                                     sort_keys=True))
        output_datasets = []
        for _, datasets_without_versions in output_datasets_tree.items():
            for _, datasets in datasets_without_versions.items():
                if datasets:
                    output_datasets.append(sorted(datasets)[-1])

        def tier_level_comparator(dataset):
            dataset_tier = dataset.split('/')[-1:][0]
            if dataset_tier in output_datatiers_set:
                return output_datatiers.index(dataset_tier)

            return -1

        output_datasets = sorted(output_datasets, key=tier_level_comparator)
        self.logger.debug('Output datasets:\n%s',
                          json.dumps(output_datasets,
                                     indent=2,
                                     sort_keys=True))
        return output_datasets

    def update_workflows(self, request):
        """
        Update computing workflows from Stats2
        """
        prepid = request.get_prepid()
        request_db = Database('requests')
        with self.locker.get_lock(prepid):
            request_json = request_db.get(prepid)
            request = Request(json_input=request_json)
            workflow_names = {w['name'] for w in request.get('workflows')}
            stats_workflows = get_workflows_from_stats_for_prepid(prepid)
            workflow_names -= {w['RequestName'] for w in stats_workflows}
            self.logger.info('%s workflows that are not in stats: %s',
                             len(workflow_names),
                             workflow_names)
            stats_workflows += get_workflows_from_stats(list(workflow_names))
            all_workflows = {}
            for workflow in stats_workflows:
                if not workflow or not workflow.get('RequestName'):
                    raise RuntimeError('Could not find workflow in Stats2')

                name = workflow.get('RequestName')
                all_workflows[name] = workflow
                self.logger.info('Found workflow %s for %s', name, prepid)

            output_datasets = self.get_output_datasets(request, all_workflows)
            workflows = self.pick_workflows(all_workflows, output_datasets)
            newest_workflow = None
            for workflow in reversed(workflows):
                workflow_name = workflow['name']
                if workflow['type'].lower() == 'resubmission':
                    self.logger.debug('Skipping %s because resubmission', workflow_name)
                    continue

                status_history = set(x['status'] for x in workflow.get('status_history', []))
                if DEAD_WORKFLOW_STATUS & status_history:
                    self.logger.debug('Skipping %s because dead', workflow_name)
                    continue

                if not newest_workflow:
                    newest_workflow = all_workflows[workflow_name]

                completed_events = -1
                for output_dataset in workflow.get('output_datasets', []):
                    if output_datasets and output_dataset['name'] == output_datasets[-1]:
                        completed_events = output_dataset['events']
                        break

                if completed_events != -1:
                    request.set('completed_events', completed_events)
                    break

            if newest_workflow:
                if 'RequestPriority' in newest_workflow:
                    priority = newest_workflow['RequestPriority']
                    request.set('priority', priority)
                    self.logger.info('Setting %s priority to %s', prepid, priority)

                if 'TotalEvents' in newest_workflow:
                    total_events = max(0, newest_workflow['TotalEvents'])
                    request.set('total_events', total_events)
                    self.logger.info('Setting %s total events to %s', prepid, total_events)

            request.set('output_datasets', output_datasets)
            request.set('workflows', workflows)
            request_db.save(request.get_json())

            if output_datasets:
                subsequent_requests = request_db.query(f'input.request={prepid}')
                self.logger.info('Found %s subsequent requests for %s: %s',
                                 len(subsequent_requests),
                                 prepid,
                                 [r['prepid'] for r in subsequent_requests])
                for subsequent_request_json in subsequent_requests:
                    subsequent_request_prepid = subsequent_request_json.get('prepid')
                    self.update_input_dataset(self.get(subsequent_request_prepid))

        return request

    def option_reset(self, prepid):
        """
        Fetch and overwrite values from subcampaign
        """
        request_db = Database('requests')
        with self.locker.get_nonblocking_lock(prepid):
            request = self.get(prepid)
            if request.get('status') != 'new':
                raise AssertionError('It is not allowed to reset '
                                     'requests that are not in status "new"')

            subcampaign_db = Database('subcampaigns')
            subcampaign_name = request.get('subcampaign')
            subcampaign_json = subcampaign_db.get(subcampaign_name)
            if not subcampaign_json:
                raise AssertionError(f'Subcampaign "{subcampaign_name}" does not exist')

            subcampaign = Subcampaign(json_input=subcampaign_json)
            request.set('memory', subcampaign.get('memory'))
            request.set('sequences', subcampaign.get('sequences'))
            request.set('energy', subcampaign.get('energy'))
            request.set('cmssw_release', subcampaign.get('cmssw_release'))
            request.set('enable_harvesting', subcampaign.get('enable_harvesting'))
            request_db.save(request.get_json())

        return request

    def change_request_priority(self, request, priority):
        """
        Change request priority
        """
        prepid = request.get_prepid()
        request_db = Database('requests')
        self.logger.info('Will try to change %s priority to %s', prepid, priority)
        if request.get('status') != 'submitted':
            raise AssertionError('It is not allowed to change priority of '
                                 'requests that are not in status "submitted"')

        request.set('priority', priority)
        active_workflows = self.pick_active_workflows(request)
        workflow_names = [w['name'] for w in active_workflows]
        change_workflow_priority(workflow_names, priority)
        # Update priority in Stats2
        refresh_workflows_in_stats(workflow_names)
        # Finally save the request
        request_db.save(request.get_json())

        return request

    def pick_active_workflows(self, request):
        """
        Filter out workflows that are rejected, aborted or failed
        """
        prepid = request.get_prepid()
        workflows = request.get('workflows')
        active_workflows = []
        for workflow in workflows:
            status_history = set(x['status'] for x in workflow.get('status_history', []))
            if not DEAD_WORKFLOW_STATUS & status_history:
                active_workflows.append(workflow)

        self.logger.info('Active workflows of %s are %s',
                         prepid,
                         ', '.join([x['name'] for x in active_workflows]))
        return active_workflows

    def reject_workflows(self, workflows):
        """
        Reject or abort list of workflows in ReqMgr2
        """
        workflow_status_pairs = []
        for workflow in workflows:
            workflow_name = workflow['name']
            status_history = workflow.get('status_history')
            if not status_history:
                self.logger.error('%s has no status history', workflow_name)
                status_history = [{'status': '<unknown>'}]

            last_workflow_status = status_history[-1]['status']
            workflow_status_pairs.append((workflow_name, last_workflow_status))

        cmsweb_reject_workflows(workflow_status_pairs)
