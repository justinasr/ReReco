"""
Module that contains RequestController class
"""
import json
import time
from core.controller.controller_base import ControllerBase
from core.model.request import Request
from core.model.subcampaign import Subcampaign
from core.database.database import Database
from core.model.subcampaign_ticket import SubcampaignTicket
from core.utils.request_submitter import RequestSubmitter
from core.utils.connection_wrapper import ConnectionWrapper
from core.utils.settings import Settings


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
            raise Exception(f'Subcampaign "{subcampaign_name}" does not exist')

        request_db = Database(self.database_name)
        subcampaign = Subcampaign(json_input=subcampaign_json)

        json_data['cmssw_release'] = subcampaign.get('cmssw_release')
        json_data['subcampaign'] = subcampaign.get_prepid()
        json_data['step'] = subcampaign.get('step')
        new_request = Request(json_input=json_data)
        if not json_data.get('sequences'):
            new_request.set('sequences', subcampaign.get('sequences'))

        if not json_data.get('memory'):
            new_request.set('memory', subcampaign.get('memory'))

        if not json_data.get('energy'):
            new_request.set('energy', subcampaign.get('energy'))

        input_dataset = new_request.get('input_dataset')
        input_dataset_parts = [x for x in input_dataset.split('/') if x]
        era = input_dataset_parts[1].split('-')[0]
        dataset = input_dataset_parts[0]
        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{dataset}-{processing_string}'
        with self.locker.get_lock(f'create-request-{prepid_middle_part}'):
            # Get a new serial number
            serial_number = self.get_highest_serial_number(request_db,
                                                           f'ReReco-{prepid_middle_part}-*')
            serial_number += 1
            # Form a new temporary prepid
            prepid = f'ReReco-{prepid_middle_part}-{serial_number:05d}'
            new_request.set('prepid', prepid)
            new_request_json = super().create(new_request.get_json())

        return new_request_json

    def check_for_update(self, old_obj, new_obj, changed_values):
        if old_obj.get('status') != 'submitting':
            raise Exception('You are now allowed to update request while it is being submitted')

        return True

    def check_for_delete(self, obj):
        if obj.get('status') != 'submitting':
            raise Exception('You are now allowed to update request while it is being submitted')

        return True

    def before_delete(self, obj):
        prepid = obj.get_prepid()
        subcampaign_tickets_db = Database('subcampaign_tickets')
        subcampaign_tickets = subcampaign_tickets_db.query(f'created_requests={prepid}')
        self.logger.debug(json.dumps(subcampaign_tickets, indent=2))
        for subcampaign_ticket_json in subcampaign_tickets:
            ticket_prepid = subcampaign_ticket_json['prepid']
            with self.locker.get_lock(ticket_prepid):
                subcampaign_ticket_json = subcampaign_tickets_db.get(ticket_prepid)
                subcampaign_ticket = SubcampaignTicket(json_input=subcampaign_ticket_json)
                subcampaign_ticket.set('created_requests', [x for x in subcampaign_ticket.get('created_requests') if x != prepid])
                subcampaign_ticket.add_history('remove_request', prepid, None)
                subcampaign_tickets_db.save(subcampaign_ticket.get_json())

        return True

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        new = not bool(obj.get_prepid())
        editing_info['prepid'] = False
        editing_info['history'] = False
        editing_info['cmssw_release'] = False
        editing_info['step'] = False
        editing_info['input_dataset'] = new
        editing_info['processing_string'] = new
        editing_info['subcampaign'] = new
        editing_info['energy'] = True
        editing_info['sequences'] = new
        status = obj.get('status')
        if status != 'new':
            editing_info['memory'] = False
            editing_info['runs'] = False
            editing_info['sequences'] = False
            editing_info['time_per_event'] = False
            editing_info['size_per_event'] = False

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
        database_url = Settings().get('cmsweb_db_url')
        command = '#!/bin/bash\n\n'
        command += request.get_cmssw_setup()
        command += '\n\n'
        # Add path to WMCore
        # This should be done in a smarter way
        command += '\n'.join([f'git clone --quiet https://github.com/dmwm/WMCore.git',
                              f'export PYTHONPATH=$(pwd)/WMCore/src/python/:$PYTHONPATH'])
        common_part = f'python config_uploader.py --file %s.py --label %s --group ppd --user $(echo $USER) --db {database_url}'
        for configs in request.get_config_file_names():
            # Run config uploader
            command += '\n'
            command += common_part % (configs['config'], configs['config'])
            if configs.get('harvest'):
                command += '\n'
                command += common_part % (configs['harvest'], configs['harvest'])

        return command

    def get_job_dict(self, request):
        """
        Return a dictionary for ReqMgr2
        """
        sequences = request.get('sequences')
        input_dataset = request.get('input_dataset')
        input_dataset_parts = [x.strip() for x in input_dataset.split('/') if x.strip()]
        acquisition_era = input_dataset_parts[1].split('-')[0]
        subcampaigns_db = Database('subcampaigns')
        subcampaign_name = request.get('subcampaign')
        subcampaign_json = subcampaigns_db.get(subcampaign_name)
        database_url = Settings().get('cmsweb_db_url')
        processing_string = request.get('processing_string')
        job_dict = {}
        job_dict['CMSSWVersion'] = request.get('cmssw_release')
        job_dict['ScramArch'] = subcampaign_json.get('scram_arch')
        job_dict['RequestPriority'] = request.get('priority')
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
        job_dict['RequestString'] = f'{input_dataset_parts[1]}_{input_dataset_parts[0]}_{processing_string}'
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

    def update_status(self, request, status):
        """
        Set new status to request, update history accordingly and save to database
        """
        request_db = Database(self.database_name)
        request.set('status', status)
        request.add_history('status', status, None)
        request_db.save(request.get_json())

    def next_status(self, request):
        """
        Trigger request to move to next status
        """
        prepid = request.get_prepid()
        with self.locker.get_nonblocking_lock(prepid):
            if request.get('status') == 'new':
                self.update_status(request, 'approved')
                return request

            if request.get('status') == 'approved':
                self.update_status(request, 'submitting')
                RequestSubmitter().add_request(request, self)
                return request

            if request.get('status') == 'submitting':
                raise Exception('You are not allowed to set next status while request is being submitted')

            if request.get('status') == 'submitted':
                raise Exception('You are not allowed to set next status while request is submitted')

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
                self.update_status(request, 'new')
            elif request.get('status') == 'submitting':
                self.update_status(request, 'approved')
            elif request.get('status') == 'submitted':
                request.set('workflows', [])
                for sequence in request.get('sequences'):
                    sequence.set('config_id', '')
                    sequence.set('harvesting_config_id', '')

                self.update_status(request, 'approved')

        return request

    def get_runs_for_request(self, request):
        """
        Return a list of runs for given request
        """
        subcampaign_db = Database('subcampaigns')
        subcampaign = subcampaign_db.get(request.get('subcampaign'))
        runs_json_path = subcampaign.get('runs_json_path')
        input_dataset = request.get('input_dataset')
        if not runs_json_path:
            return []

        if not input_dataset:
            return []

        with self.locker.get_lock('get-request-runs'):
            start_time = time.time()
            dbs_conn = ConnectionWrapper()
            dbs_response = dbs_conn.api('GET',
                                        f'/dbs/prod/global/DBSReader/runs?dataset={input_dataset}')
            dbs_response = json.loads(dbs_response.decode('utf-8'))
            if not dbs_response:
                return []

            dbs_runs = dbs_response[0].get('run_num', [])
            cert_conn = ConnectionWrapper(host='cms-service-dqm.web.cern.ch')
            cert_response = cert_conn.api('GET',
                                          f'/cms-service-dqm/CAF/certification/{runs_json_path}')

        cert_response = json.loads(cert_response.decode('utf-8'))
        certification_runs = [int(x) for x in list(cert_response.keys())]
        all_runs = list(set(dbs_runs).intersection(set(certification_runs)))
        end_time = time.time()
        self.logger.info('Got %s runs from DBS for dataset %s and %s runs from '
                         'certification JSON in %.2fs. Intersection yielded %s runs',
                         len(dbs_runs),
                         input_dataset,
                         len(certification_runs),
                         end_time - start_time,
                         len(all_runs))

        return all_runs
