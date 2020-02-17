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
from core.utils.cmsweb import ConnectionWrapper
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
        request_db = Database('requests')
        # Get a subcampaign
        subcampaign_db = Database('subcampaigns')
        subcampaign_name = json_data.get('subcampaign')
        if not subcampaign_name:
            raise Exception('No subcampaigns name is given')

        subcampaign_json = subcampaign_db.get(subcampaign_name)
        if not subcampaign_json:
            raise Exception(f'Campaign "{subcampaign_name}" does not exist')

        subcampaign = Subcampaign(json_input=subcampaign_json)
        # Clean up the request input
        json_data['history'] = []
        if '_rev' in json_data:
            del json_data['_rev']

        if '_id' in json_data:
            del json_data['_id']

        json_data['prepid'] = 'ReReco-Temp-00000'
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
        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{input_dataset_parts[0]}-{processing_string}'
        with self.locker.get_lock(f'generate-prepid-{prepid_middle_part}'):
            # Get a new serial number
            serial_numbers = request_db.query(f'prepid=ReReco-{prepid_middle_part}-*',
                                              limit=1,
                                              sort_asc=False)
            if not serial_numbers:
                serial_number = 0
            else:
                serial_number = serial_numbers[0]['prepid']
                serial_number = int(serial_number.split('-')[-1])

            serial_number += 1
            # Form a new temporary prepid
            prepid = f'ReReco-{prepid_middle_part}-{serial_number:05d}'
            new_request.set('prepid', prepid)
            self.logger.info('Generated prepid %s', (prepid))
            new_request.add_history('create', prepid, None)
            if not self.check_for_create(new_request):
                self.logger.error('Error while checking new item %s', prepid)
                return None

            if not request_db.save(new_request.get_json()):
                raise Exception(f'Error saving {prepid}')

            return new_request.get_json()

    def check_for_create(self, obj):
        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        return True

    def check_for_delete(self, obj):
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
        editing_info = {k: not k.startswith('_') for k in obj.get_json().keys()}
        newly_created = not bool(editing_info.get('prepid'))
        editing_info['prepid'] = False
        editing_info['history'] = False
        editing_info['cmssw_release'] = False
        editing_info['step'] = False
        editing_info['input_dataset'] = newly_created
        editing_info['processing_string'] = newly_created
        editing_info['subcampaign'] = newly_created
        editing_info['energy'] = True
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
        """
        self.logger.debug('Getting cmsDriver commands for %s', request.get_prepid())
        number_of_sequences = len(request.get('sequences'))
        cms_driver = '#!/bin/bash\n\n'
        cms_driver += request.get_cmssw_setup()
        cms_driver += '\n\n'
        for i in range(number_of_sequences):
            if i == 0 and for_submission:
                cms_driver += request.get_cmsdriver(i, '_placeholder_.root')
            else:
                cms_driver += request.get_cmsdriver(i)
            cms_driver += '\n\n'

        return cms_driver

    def get_config_upload_file(self, request):
        self.logger.debug('Getting config upload script for %s', request.get_prepid())
        prepid = request.get_prepid()
        database_url = Settings().get('cmsweb_db_url')
        command = '#!/bin/bash\n\n'
        command += request.get_cmssw_setup()
        command += '\n\n'
        # Add path to WMCore
        # This should be done in a smarter way
        command += '\n'.join([f'git clone https://github.com/dmwm/WMCore.git',
                              f'export PYTHONPATH=$(pwd)/WMCore/src/python/:$PYTHONPATH'])
        number_of_sequences = len(request.get('sequences'))
        for i in range(number_of_sequences):
            # Run config uploader
            command += f'\npython config_uploader.py --file {prepid}_{i}_cfg.py --label {prepid}_{i} --group ppd --user $(echo $USER) --db {database_url}'
            sequence = request.get('sequences')[i]
            if sequence.needs_harvesting():
                command += f'\npython config_uploader.py --file {prepid}_{i}_harvest_cfg.py --label {prepid}_{i}_harvest --group ppd --user $(echo $USER) --db {database_url}'

        return command

    def get_job_dict(self, request):
        """
        Return a dictionary for ReqMgr2
        """
        subcampaigns_db = Database('subcampaigns')
        subcampaign_json = subcampaigns_db.get(request.get('subcampaign'))
        sequences = request.get('sequences')
        if len(sequences) == 0:
            return {}

        seq = request.get('sequences')[0]
        job_dict = {}
        job_dict['CMSSWVersion'] = request.get('cmssw_release')
        job_dict['ScramArch'] = subcampaign_json.get('scram_arch')
        job_dict['RequestPriority'] = request.get('priority')
        job_dict['RunWhitelist'] = []
        job_dict['InputDataset'] = request.get('input_dataset')
        job_dict['RunBlacklist'] = []
        job_dict['BlockWhitelist'] = []
        job_dict['BlockBlacklist'] = []
        job_dict['RequestType'] = 'ReReco'
        job_dict['GlobalTag'] = seq.get('conditions')
        job_dict['Group'] = 'PPD'
        job_dict['Requestor'] = 'pdmvserv'
        job_dict['Campaign'] = request.get('subcampaign').split('-')[0]
        job_dict['Memory'] = request.get('memory')
        job_dict['SizePerEvent'] = request.get('size_per_event')
        job_dict['TimePerEvent'] = request.get('time_per_event')
        job_dict['EnableHarvesting'] = False
        job_dict['ProcessingString'] = request.get('processing_string')
        job_dict['Multicore'] = seq.get('nThreads')
        job_dict['PrepID'] = request.get_prepid()
        job_dict['ConfigCacheID'] = seq.get('config_id')
        job_dict['DQMConfigCacheID'] = seq.get('harvesting_config_id')
        input_dataset = request.get('input_dataset')
        input_dataset_parts = [x.strip() for x in input_dataset.split('/') if x.strip()]
        processing_string = request.get('processing_string')
        job_dict['RequestString'] = f'{input_dataset_parts[1]}_{input_dataset_parts[0]}_{processing_string}'
        job_dict['AcquisitionEra'] = input_dataset_parts[1].split('-')[0]
        database_url = Settings().get('cmsweb_db_url')
        job_dict['ConfigCacheUrl'] = database_url
        job_dict['CouchURL'] = database_url

        return job_dict

    def next_status(self, request):
        """
        Trigger request to move to next status
        """
        if request.get('status') == 'new':
            request.set('status', 'approved')
            self.update(request.get_json())
            return request

        if request.get('status') == 'approved':
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
        request_db = Database('requests')
        if request.get('status') == 'approved':
            request.set('status', 'new')
            self.update(request.get_json())
            return request

        if request.get('status') == 'submitting':
            request.set('status', 'approved')
            self.update(request.get_json())
            return request

        if request.get('status') == 'submitted':
            request.set('status', 'approved')
            for sequence in request.get('sequences'):
                sequence.set('config_id', '')
                sequence.set('harvesting_config_id', '')

            request_db.save(request.get_json())
            return request

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
        self.logger.debug('Sleeping for %.2fs', max(end_time - start_time, 10) * 0.1)
        time.sleep(max(end_time - start_time, 10) * 0.1)
        self.logger.info('Got %s runs from DBS for dataset %s and %s runs from '
                         'certification JSON in %.2fs. Intersection yielded %s runs',
                         len(dbs_runs),
                         input_dataset,
                         len(certification_runs),
                         end_time - start_time,
                         len(all_runs))

        return all_runs
