"""
Module that contains RequestController class
"""
import json
import time
from core_lib.database.database import Database
from core_lib.utils.settings import Settings
from core_lib.utils.ssh_executor import SSHExecutor
from core_lib.utils.connection_wrapper import ConnectionWrapper
import core_lib.controller.controller_base as controller_base
from core.model.request import Request
from core.model.subcampaign import Subcampaign
from core.model.ticket import Ticket
from core.utils.request_submitter import RequestSubmitter


class RequestController(controller_base.ControllerBase):
    """
    Controller that has all actions related to a request
    """

    def __init__(self):
        controller_base.ControllerBase.__init__(self)
        self.database_name = 'requests'
        self.model_class = Request

    def create(self, json_data):
        # Get a subcampaign
        subcampaign_db = Database('subcampaigns')
        subcampaign_name = json_data.get('subcampaign')
        subcampaign_json = subcampaign_db.get(subcampaign_name)
        if not subcampaign_json:
            raise Exception(f'Subcampaign "{subcampaign_name}" does not exist')

        request_db = Database(self.database_name)
        subcampaign = Subcampaign(json_input=subcampaign_json)

        json_data['cmssw_release'] = subcampaign.get('cmssw_release')
        json_data['subcampaign'] = subcampaign.get_prepid()
        json_data['prepid'] = 'PlaceholderPrepID'
        new_request = Request(json_input=json_data)
        if not json_data.get('sequences'):
            new_request.set('sequences', subcampaign.get('sequences'))

        if not json_data.get('memory'):
            new_request.set('memory', subcampaign.get('memory'))

        if not json_data.get('energy'):
            new_request.set('energy', subcampaign.get('energy'))

        request_input = new_request.get('input')
        input_dataset = request_input.get('dataset')
        input_request_prepid = request_input.get('request')
        # Prepid is made of era, dataset and processing string
        # Either they are taken from input dataset or input request
        # Only one must be provided
        self.logger.info(request_input)
        if input_dataset and input_request_prepid:
            raise Exception(f'Request cannot have both input request and input dataset, only one')

        if input_dataset and not input_request_prepid:
            input_dataset_parts = [x for x in input_dataset.split('/') if x]
            era = input_dataset_parts[1].split('-')[0]
            dataset = input_dataset_parts[0]
        elif not input_dataset and input_request_prepid:
            input_request_json = request_db.get(input_request_prepid)
            if not input_request_json:
                raise Exception(f'Request "{input_request_prepid}" does not exist')

            input_request = Request(json_input=input_request_json)
            era = input_request.get_era()
            dataset = input_request.get_dataset()
        else:
            raise Exception(f'Request must have either a input request or input dataset')

        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{dataset}-{processing_string}'
        settings = Settings()
        with self.locker.get_lock(f'create-request-prepid'):
            # Get a new serial number
            serial_number = self.get_highest_serial_number(request_db,
                                                           f'ReReco-{prepid_middle_part}-*')
            serial_numbers = settings.get('requests_prepid_sequence', {})
            serial_number = max(serial_number, serial_numbers.get(prepid_middle_part, 0))
            serial_number += 1
            # Form a new temporary prepid
            prepid = f'ReReco-{prepid_middle_part}-{serial_number:05d}'
            new_request.set('prepid', prepid)
            new_request_json = super().create(new_request.get_json())
            # After successful save update serial numbers in settings
            serial_numbers[prepid_middle_part] = serial_number
            settings.save('requests_prepid_sequence', serial_numbers)

        return new_request_json

    def check_for_update(self, old_obj, new_obj, changed_values):
        if old_obj.get('status') == 'submitting':
            raise Exception('You are now allowed to update request while it is being submitted')

        return True

    def check_for_delete(self, obj):
        if obj.get('status') != 'new':
            raise Exception('Request must be in status "new" before it is deleted')

        requests_db = Database('requests')
        prepid = obj.get_prepid()
        subsequent_requests_query = f'input.request={prepid}'
        subsequent_requests = requests_db.query(subsequent_requests_query)
        if subsequent_requests:
            subsequent_requests_prepids = ', '.join([r['prepid'] for r in subsequent_requests])
            raise Exception(f'Request cannot be deleted because it is input request'
                            f'for {subsequent_requests_prepids}. Delete these requests first')

        return True

    def before_update(self, obj):
        if obj.get('status') == 'submitted':
            old_obj = self.get(obj.get_prepid())
            if old_obj.get('priority') != obj.get('priority'):
                self.change_request_priority(obj, obj.get('priority'))

    def before_delete(self, obj):
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
        editing_info['memory'] = status_new
        editing_info['input'] = status_new
        editing_info['runs'] = status_new
        editing_info['time_per_event'] = status_new
        editing_info['size_per_event'] = status_new

        return editing_info

    def get_cmsdriver(self, request, for_submission=False):
        """
        Get bash script with cmsDriver commands for a given request
        If script will be used for submission, replace input file with placeholder
        """
        self.logger.debug('Getting cmsDriver commands for %s', request.get_prepid())
        cms_driver = '#!/bin/bash\n\n'
        cms_driver += request.get_cmssw_setup()
        cms_driver += '\n\n'
        if for_submission:
            cms_driver += request.get_cmsdrivers('_placeholder_.root')
        else:
            cms_driver += request.get_cmsdrivers()

        cms_driver += '\n\n'

        return cms_driver

    def get_config_upload_file(self, request):
        """
        Get bash script that would upload config files to ReqMgr2
        """
        self.logger.debug('Getting config upload script for %s', request.get_prepid())
        database_url = Settings().get('cmsweb_url') + '/couchdb'
        command = '#!/bin/bash\n'
        common_check_part = 'if [ ! -s "%s.py" ]; then\n'
        common_check_part += '  echo "File %s.py is missing" >&2\n'
        common_check_part += '  exit 1\n'
        common_check_part += 'fi\n'
        for configs in request.get_config_file_names():
            # Run config uploader
            command += '\n'
            command += common_check_part % (configs['config'], configs['config'])
            if configs.get('harvest'):
                command += '\n'
                command += common_check_part % (configs['harvest'], configs['harvest'])

        command += '\n'
        command += request.get_cmssw_setup()
        command += '\n\n'
        # Add path to WMCore
        # This should be done in a smarter way
        command += '\n'.join(['git clone --quiet https://github.com/dmwm/WMCore.git',
                              'export PYTHONPATH=$(pwd)/WMCore/src/python/:$PYTHONPATH'])
        common_upload_part = ('python config_uploader.py --file %s.py --label %s '
                              f'--group ppd --user $(echo $USER) --db {database_url}')
        for configs in request.get_config_file_names():
            # Run config uploader
            command += '\n'
            command += common_upload_part % (configs['config'], configs['config'])
            if configs.get('harvest'):
                command += '\n'
                command += common_upload_part % (configs['harvest'], configs['harvest'])

        # Remove WMCore in order not to run out of space
        command += '\n'
        command += 'rm -rf WMCore'
        command += '\n'
        cmssw_release = request.get('cmssw_release')
        command += f'rm -rf {cmssw_release}'

        return command

    def get_job_dict(self, request):
        """
        Return a dictionary for ReqMgr2
        """
        prepid = request.get_prepid()
        self.logger.debug('Getting job dict for %s', prepid)
        sequences = request.get('sequences')
        input_dataset = request.get('input')['dataset']
        acquisition_era = request.get_era()
        subcampaigns_db = Database('subcampaigns')
        subcampaign_name = request.get('subcampaign')
        subcampaign_json = subcampaigns_db.get(subcampaign_name)
        database_url = Settings().get('cmsweb_url') + '/couchdb'
        processing_string = request.get('processing_string')
        request_string = request.get_request_string()
        job_dict = {}
        job_dict['CMSSWVersion'] = request.get('cmssw_release')
        job_dict['ScramArch'] = subcampaign_json.get('scram_arch')
        job_dict['RequestPriority'] = request.get('priority')
        if input_dataset:
            job_dict['InputDataset'] = input_dataset

        job_dict['Group'] = 'PPD'
        job_dict['Requestor'] = 'pdmvserv'
        job_dict['Campaign'] = request.get('subcampaign').split('-')[0]
        job_dict['Memory'] = request.get('memory')
        job_dict['ConfigCacheUrl'] = database_url
        job_dict['CouchURL'] = database_url
        job_dict['PrepID'] = request.get_prepid()
        job_dict['AcquisitionEra'] = acquisition_era
        job_dict['ProcessingString'] = processing_string
        job_dict['RequestType'] = 'ReReco'
        job_dict['SizePerEvent'] = request.get('size_per_event')
        job_dict['TimePerEvent'] = request.get('time_per_event')
        job_dict['RequestString'] = request_string
        job_dict['EnableHarvesting'] = False
        job_dict['RunWhitelist'] = request.get('runs')
        job_dict['RunBlacklist'] = []
        job_dict['BlockWhitelist'] = []
        job_dict['BlockBlacklist'] = []
        if len(sequences) == 1:
            first_sequence = request.get('sequences')[0]
            job_dict['GlobalTag'] = first_sequence.get('conditions')
            job_dict['Multicore'] = first_sequence.get('nThreads')
            if first_sequence.get('config_id'):
                job_dict['ConfigCacheID'] = first_sequence.get('config_id')

            if first_sequence.get('harvesting_config_id'):
                job_dict['DQMConfigCacheID'] = first_sequence.get('harvesting_config_id')

            job_dict['Scenario'] = first_sequence.get('scenario')
        elif len(sequences) > 1:
            raise NotImplementedError('Multiple sequences are not yet supported')

        return job_dict

    def update_input_dataset(self, request):
        """
        Update input dataset name from input request (if exists)
        Update runs from input request if they are not specified yet
        """
        prepid = request.get_prepid()
        input_request_prepid = request.get('input')['request']
        if input_request_prepid:
            input_request = self.get(input_request_prepid)
            input_dataset = input_request.get('input')['dataset']
            output_datasets = input_request.get('output_datasets')
            should_update = False
            if output_datasets and input_dataset != output_datasets[-1]:
                request.get('input')['dataset'] = output_datasets[-1]
                should_update = True
            elif not output_datasets:
                request.get('input')['dataset'] = ''
                should_update = True

            if not request.get('runs'):
                request.set('runs', input_request.get('runs'))
                should_update = True

            if should_update:
                self.update(request.get_json(), force_update=True)
        else:
            self.logger.info('Did not update %s input dataset', prepid)

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
                return self.move_request_to_approved(request)

            if request.get('status') == 'approved':
                return self.move_request_to_submitting(request)

            if request.get('status') == 'submitting':
                raise Exception('Request is being submitted')

            if request.get('status') == 'submitted':
                return self.move_request_to_done(request)

            if request.get('status') == 'done':
                raise Exception('Request is already done')

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

        return request

    def move_request_to_approved(self, request):
        """
        Try to move rquest to approved
        """
        self.update_input_dataset(request)
        prepid = request.get_prepid()
        if not request.get('runs'):
            raise Exception(f'No runs are specified in {prepid}')

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
            raise Exception(f'Could not move {prepid} to submitting '
                            'because it does not have input dataset')

        # Make sure input dataset is VALID
        dbs_conn = ConnectionWrapper(host='cmsweb.cern.ch')
        dbs_response = dbs_conn.api('POST',
                                    '/dbs/prod/global/DBSReader/datasetlist',
                                    {'dataset': input_dataset,
                                     'detail': 1})
        dbs_response = json.loads(dbs_response.decode('utf-8'))
        dataset_access_type = dbs_response[0].get('dataset_access_type', 'unknown')
        self.logger.info('%s access type is %s', input_dataset, dataset_access_type)
        if dataset_access_type != 'VALID':
            raise Exception(f'{input_dataset} type is {dataset_access_type}, it must be VALID')

        RequestSubmitter().add_request(request, self)
        self.update_status(request, 'submitting')
        return request

    def move_request_to_done(self, request):
        """
        Try to move request to done status
        """
        prepid = request.get_prepid()
        request = self.update_workflows(request)
        workflows = request.get('workflows')
        if workflows:
            last_workflow = workflows[-1]
            for output_dataset in last_workflow['output_datasets']:
                dataset_type = output_dataset['type']
                if dataset_type.lower() != 'valid':
                    dataset_name = output_dataset['name']
                    raise Exception(f'Could not move {prepid} to "done" '
                                    f'because {dataset_name} is {dataset_type}')

            for status in last_workflow['status_history']:
                if status['status'].lower() == 'completed':
                    completed_timestamp = status['time']
                    break
            else:
                last_workflow_name = last_workflow['name']
                raise Exception(f'Could not move {prepid} to "done" because '
                                f'{last_workflow_name} is not yet "completed"')

            self.update_status(request, 'done', completed_timestamp)
            # Submit all subsequent requests
            self.submit_subsequent_requests(request)
        else:
            raise Exception(f'{prepid} does not have any workflows in computing')

        return request

    def submit_subsequent_requests(self, request):
        """
        Submit all requests that have given request as input
        """
        request_db = Database('requests')
        prepid = request.get_prepid()
        query = f'input.request={prepid}'
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
                if subsequent_request.get('status') == 'new':
                    self.next_status(subsequent_request)

                if subsequent_request.get('status') == 'approved':
                    self.next_status(subsequent_request)

            except Exception as ex:
                self.logger.error('Error moving %s to next status: %s',
                                  subsequent_request_prepid,
                                  ex)

    def move_request_back_to_new(self, request):
        """
        Try to move rquest back to new
        """
        self.update_status(request, 'new')
        return request

    def move_request_back_to_approved(self, request):
        """
        Try to move rquest back to approved
        """
        active_workflows = self.__pick_active_workflows(request)
        self.force_stats_to_refresh([x['name'] for x in active_workflows])
        # Take active workflows again in case any of them changed during Stats refresh
        active_workflows = self.__pick_active_workflows(request)
        if active_workflows:
            self.__reject_workflows(active_workflows)

        request.set('workflows', [])
        request.set('total_events', 0)
        request.set('completed_events', 0)
        for sequence in request.get('sequences'):
            sequence.set('config_id', '')
            sequence.set('harvesting_config_id', '')

        self.update_status(request, 'approved')
        return request

    def get_runs(self, subcampaign_name, input_dataset):
        """
        Return a list of runs for given input dataset in a subcampaign
        """
        subcampaign_db = Database('subcampaigns')
        subcampaign = subcampaign_db.get(subcampaign_name)
        runs_json_path = subcampaign.get('runs_json_path')
        with self.locker.get_lock('get-request-runs'):
            start_time = time.time()
            dbs_runs = []
            if input_dataset:
                dbs_conn = ConnectionWrapper(host='cmsweb.cern.ch')
                dbs_response = dbs_conn.api(
                    'GET',
                    f'/dbs/prod/global/DBSReader/runs?dataset={input_dataset}'
                )
                dbs_response = json.loads(dbs_response.decode('utf-8'))
                if dbs_response:
                    dbs_runs = dbs_response[0].get('run_num', [])

            json_runs = []
            if runs_json_path:
                json_conn = ConnectionWrapper(host='cms-service-dqm.web.cern.ch')
                json_response = json_conn.api(
                    'GET',
                    f'/cms-service-dqm/CAF/certification/{runs_json_path}'
                )
                json_response = json.loads(json_response.decode('utf-8'))
                if json_response:
                    json_runs = [int(x) for x in list(json_response.keys())]

        all_runs = []
        dbs_runs = set(dbs_runs)
        json_runs = set(json_runs)
        if dbs_runs and json_runs:
            all_runs = dbs_runs & json_runs
        else:
            all_runs = dbs_runs | json_runs

        all_runs = sorted(list(all_runs))
        end_time = time.time()
        self.logger.info('Got %s runs from DBS for dataset %s and %s runs '
                         'from JSON in %.2fs. Result is %s runs',
                         len(dbs_runs),
                         input_dataset,
                         len(json_runs),
                         end_time - start_time,
                         len(all_runs))

        return all_runs

    def get_runs_for_request(self, request):
        """
        Return a list of runs for given request
        """
        subcampaign_name = request.get('subcampaign')
        input_dataset = request.get('input')['dataset']
        return self.get_runs(subcampaign_name, input_dataset)

    def __pick_workflows(self, all_workflows, output_datasets):
        """
        Pick, process and sort workflows from computing based on output datasets
        """
        new_workflows = []
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

    def __get_output_datasets(self, request, all_workflows):
        """
        Return a list of sorted output datasets for request from given workflows
        """
        output_datatiers = []
        prepid = request.get_prepid()
        for sequence in request.get('sequences'):
            output_datatiers.extend(sequence.get('datatier'))

        output_datatiers = set(output_datatiers)
        self.logger.info('%s output datatiers are: %s', prepid, ', '.join(output_datatiers))
        output_datasets_tree = {k: {} for k in output_datatiers}
        for _, workflow in all_workflows.items():
            for output_dataset in workflow.get('OutputDatasets', []):
                output_dataset_parts = [x.strip() for x in output_dataset.split('/')]
                output_dataset_datatier = output_dataset_parts[-1]
                output_dataset_no_datatier = '/'.join(output_dataset_parts[:-1])
                output_dataset_no_version = '-'.join(output_dataset_no_datatier.split('-')[:-1])
                if output_dataset_datatier in output_datatiers:
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
            # DQMIO priority is the lowest because it does not produce any
            # events and is used only for some statistical reasons
            tier_priority = ['DQM',
                             'DQMIO',
                             'USER',
                             'ALCARECO',
                             'RAW',
                             'RECO',
                             'AOD',
                             'MINIAOD',
                             'NANOAOD']

            for (priority, tier) in enumerate(tier_priority):
                if tier == dataset_tier:
                    return priority

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
            stats_conn = ConnectionWrapper(host='vocms074.cern.ch',
                                           port=5984,
                                           https=False,
                                           keep_open=True)
            existing_workflows = request.get('workflows')
            stats_workflows = stats_conn.api(
                'GET',
                f'/requests/_design/_designDoc/_view/prepids?key="{prepid}"&include_docs=True'
            )
            stats_workflows = json.loads(stats_workflows)
            stats_workflows = [x['doc'] for x in stats_workflows['rows']]
            existing_workflows = [x['name'] for x in existing_workflows]
            stats_workflows = [x['RequestName'] for x in stats_workflows]
            all_workflow_names = list(set(existing_workflows) | set(stats_workflows))
            self.logger.info('All workflows of %s are %s', prepid, ', '.join(all_workflow_names))
            all_workflows = {}
            for workflow_name in all_workflow_names:
                workflow = stats_conn.api('GET', f'/requests/{workflow_name}')
                if not workflow:
                    raise Exception(f'Could not find {workflow_name} in Stats2')

                workflow = json.loads(workflow)
                if workflow.get('RequestType').lower() == 'resubmission':
                    continue

                all_workflows[workflow_name] = workflow
                self.logger.info('Fetched workflow %s', workflow_name)

            stats_conn.close()
            output_datasets = self.__get_output_datasets(request, all_workflows)
            new_workflows = self.__pick_workflows(all_workflows, output_datasets)
            all_workflow_names = [x['name'] for x in new_workflows]
            for new_workflow in reversed(new_workflows):
                completed_events = -1
                for output_dataset in new_workflow.get('output_datasets', []):
                    if output_datasets and output_dataset['name'] == output_datasets[-1]:
                        completed_events = output_dataset['events']
                        break

                if completed_events != -1:
                    request.set('completed_events', completed_events)
                    break

            if all_workflow_names:
                newest_workflow = all_workflows[all_workflow_names[-1]]
                if 'RequestPriority' in newest_workflow:
                    request.set('priority', newest_workflow['RequestPriority'])

                if 'TotalEvents' in newest_workflow:
                    request.set('total_events', max(0, newest_workflow['TotalEvents']))

            request.set('output_datasets', output_datasets)
            request.set('workflows', new_workflows)
            request_db.save(request.get_json())

            if output_datasets:
                query = f'input.request={prepid}'
                subsequent_requests = request_db.query(query)
                self.logger.info('Found %s subsequent requests for %s: %s',
                                 len(subsequent_requests),
                                 prepid,
                                 [r['prepid'] for r in subsequent_requests])
                for subsequent_request_json in subsequent_requests:
                    subsequent_request_prepid = subsequent_request_json.get('prepid')
                    self.update_input_dataset(self.get(subsequent_request_prepid))

        return request

    def option_reset(self, request):
        """
        Fetch and overwrite values from subcampaign
        """
        prepid = request.get_prepid()
        request_db = Database('requests')
        with self.locker.get_nonblocking_lock(prepid):
            request_json = request_db.get(prepid)
            request = Request(json_input=request_json)
            if request.get('status') != 'new':
                raise Exception('It is not allowed to option reset '
                                'requests that are not in status "new"')

            subcampaign_db = Database('subcampaigns')
            subcampaign_name = request.get('subcampaign')
            subcampaign_json = subcampaign_db.get(subcampaign_name)
            if not subcampaign_json:
                raise Exception(f'Subcampaign "{subcampaign_name}" does not exist')

            subcampaign = Subcampaign(json_input=subcampaign_json)
            request.set('memory', subcampaign.get('memory'))
            request.set('sequences', subcampaign.get('sequences'))
            request.set('energy', subcampaign.get('energy'))
            request_db.save(request.get_json())

        return request

    def change_request_priority(self, request, priority):
        """
        Change request priority
        """
        prepid = request.get_prepid()
        request_db = Database('requests')
        self.logger.info('Will try to change %s priority to %s', prepid, priority)
        with self.locker.get_nonblocking_lock(prepid):
            request_json = request_db.get(prepid)
            request = Request(json_input=request_json)
            if request.get('status') != 'submitted':
                raise Exception('It is not allowed to change priority of '
                                'requests that are not in status "submitted"')

            request.set('priority', priority)
            updated_workflows = []
            active_workflows = self.__pick_active_workflows(request)
            settings = Settings()
            connection = ConnectionWrapper(host=settings.get('cmsweb_url'), keep_open=True)
            for workflow in active_workflows:
                workflow_name = workflow['name']
                self.logger.info('Changing "%s" priority to %s', workflow_name, priority)
                response = connection.api('PUT',
                                          f'/reqmgr2/data/request/{workflow_name}',
                                          {'RequestPriority': priority})
                updated_workflows.append(workflow_name)
                self.logger.debug(response)

            connection.close()
            # Update priority in Stats2
            self.force_stats_to_refresh(updated_workflows)
            # Finally save the request
            request_db.save(request.get_json())

        return request

    def force_stats_to_refresh(self, workflows):
        """
        Force Stats2 to update workflows with given workflow names
        """
        credentials_path = Settings().get('credentials_path')
        with self.locker.get_lock('refresh-stats'):
            ssh_executor = SSHExecutor('vocms074.cern.ch', credentials_path)
            workflow_update_commands = ['cd /home/pdmvserv/private',
                                        'source setup_credentials.sh',
                                        'cd /home/pdmvserv/Stats2']
            for workflow_name in workflows:
                workflow_update_commands.append(
                    f'python3 stats_update.py --action update --name {workflow_name}'
                )

            self.logger.info('Will make Stats2 refresh these workflows: %s', ', '.join(workflows))
            ssh_executor.execute_command(workflow_update_commands)

    def __pick_active_workflows(self, request):
        """
        Filter out workflows that are rejected, aborted or failed
        """
        prepid = request.get_prepid()
        workflows = request.get('workflows')
        active_workflows = []
        inactive_statuses = {'aborted', 'rejected', 'failed'}
        for workflow in workflows:
            status_history = set(x['status'] for x in workflow.get('status_history', []))
            if not inactive_statuses & status_history:
                active_workflows.append(workflow)

        self.logger.info('Active workflows of %s are %s',
                         prepid,
                         ', '.join([x['name'] for x in active_workflows]))
        return active_workflows

    def __reject_workflows(self, workflows):
        """
        Reject or abort list of workflows in ReqMgr2
        """
        cmsweb_url = Settings().get('cmsweb_url')
        connection = ConnectionWrapper(host=cmsweb_url, keep_open=True)
        headers = {'Content-type': 'application/json',
                   'Accept': 'application/json'}
        for workflow in workflows:
            workflow_name = workflow['name']
            status_history = workflow.get('status_history')
            if not status_history:
                self.logger.error('%s has no status history', workflow_name)
                continue

            last_workflow_status = status_history[-1]['status']
            self.logger.info('%s last status is %s', workflow_name, last_workflow_status)
            # Depending on current status of workflow,
            # it might need to be either aborted or rejected
            if last_workflow_status in ('assigned',
                                        'staging',
                                        'staged',
                                        'acquired',
                                        'running-open',
                                        'running-closed'):
                new_status = 'aborted'
            else:
                new_status = 'rejected'

            self.logger.info('Will change %s status %s to %s',
                             workflow_name,
                             last_workflow_status,
                             new_status)
            reject_response = connection.api('PUT',
                                             f'/reqmgr2/data/request/{workflow_name}',
                                             {'RequestStatus': new_status},
                                             headers)
            self.logger.info(reject_response)

        connection.close()
