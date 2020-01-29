"""
Module that contains RequestController class
"""
import json
from core.controller.controller_base import ControllerBase
from core.model.request import Request
from core.model.subcampaign import Subcampaign
from core.database.database import Database
from core.model.sequence import Sequence
from core.model.subcampaign_ticket import SubcampaignTicket


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
        input_dataset = new_request.get('input_dataset')
        input_dataset_parts = [x for x in input_dataset.split('/') if x]
        era = input_dataset_parts[1].split('-')[0]
        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{input_dataset_parts[0]}-{processing_string}'
        with self.locker.get_lock(f'generate-prepid-{subcampaign_name}'):
            # Get a new serial number
            serial_numbers = request_db.query_view('serial_number',
                                                   f'key="{prepid_middle_part}"&group=true')
            if not serial_numbers:
                serial_number = 0
            else:
                serial_number = serial_numbers[0]['value']

            serial_number += 1
            # Form a new temporary prepid
            prepid = f'ReReco-{prepid_middle_part}-{serial_number:05d}'
            new_request.set('prepid', prepid)
            self.logger.info('Generated prepid %s', (prepid))
            new_request.add_history('create', prepid, None)
            if not json_data.get('sequences'):
                new_request.set('sequences', subcampaign.get('sequences'))
            if not json_data.get('memory'):
                new_request.set('memory', subcampaign.get('memory'))

            if not json_data.get('energy'):
                new_request.set('energy', subcampaign.get('energy'))

            if not self.check_for_create(new_request):
                self.logger.error('Error while checking new item %s', prepid)
                return None

            if not request_db.save(new_request.get_json()):
                raise Exception(f'Error saving {prepid}')

            return new_request.get_json()

    def get(self, prepid):
        obj = super().get(prepid)
        if obj:
            new_sequences = []
            for sequence in obj.get('sequences'):
                new_sequences.append(Sequence(json_input=sequence).get_json())

            obj.set('sequences', new_sequences)
            return obj

        return None

    def check_for_create(self, obj):
        sequences = []
        for sequence_json in obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        obj.set('sequences', sequences)
        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        sequences = []
        for sequence_json in new_obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        new_obj.set('sequences', sequences)
        return True

    def check_for_delete(self, obj):
        prepid = obj.get_prepid()
        subcampaign_tickets_db = Database('subcampaign_tickets')
        subcampaign_tickets = subcampaign_tickets_db.query(f'created_requests={prepid}')
        self.logger.debug(json.dumps(subcampaign_tickets, indent=4))
        for subcampaign_ticket_json in subcampaign_tickets:
            subcampaign_ticket = SubcampaignTicket(json_input=subcampaign_ticket_json)
            subcampaign_ticket.set('created_requests', [x for x in subcampaign_ticket.get('created_requests') if x != prepid])
            subcampaign_ticket.add_history('remove_request', prepid, None)
            subcampaign_tickets_db.save(subcampaign_ticket.get_json())

        return True

    def get_editing_info(self, obj):
        editing_info = {k: not k.startswith('_') for k in obj.get_json().keys()}
        is_new = not bool(editing_info.get('prepid'))
        editing_info['prepid'] = False
        editing_info['history'] = False
        editing_info['step'] = False
        editing_info['cmssw_release'] = False
        editing_info['input_dataset'] = is_new
        editing_info['processing_string'] = is_new
        editing_info['subcampaign'] = is_new
        editing_info['sequences'] = not is_new
        return editing_info

    def get_cmsdriver(self, request):
        """
        Get bash script with cmsDriver commands for a given request
        """
        self.logger.debug('Getting cmsDriver commands for %s', request.get_prepid())
        number_of_sequences = len(request.get('sequences'))
        cms_driver = '#!/bin/bash\n\n'
        cms_driver += request.get_cmssw_setup()
        cms_driver += '\n\n'
        for i in range(number_of_sequences):
            cms_driver += request.get_cmsdriver(i)
            cms_driver += '\n\n'

        return cms_driver
