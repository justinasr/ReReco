"""
Module that contains RequestController class
"""
import json
from core.controller.controller_base import ControllerBase
from core.model.request import Request
from core.model.campaign import Campaign
from core.database.database import Database
from core.model.sequence import Sequence
from core.model.campaign_ticket import CampaignTicket


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
        # Get a campaign
        campaign_db = Database('campaigns')
        campaign_name = json_data.get('member_of_campaign')
        if not campaign_name:
            raise Exception('No campaign name is given')

        campaign_json = campaign_db.get(campaign_name)
        if not campaign_json:
            raise Exception(f'Campaign "{campaign_name}" does not exist')

        campaign = Campaign(json_input=campaign_json)
        # Clean up the request input
        json_data['history'] = []
        if '_rev' in json_data:
            del json_data['_rev']

        if '_id' in json_data:
            del json_data['_id']

        json_data['prepid'] = 'ReReco-Temp-00000'
        json_data['cmssw_release'] = campaign.get('cmssw_release')
        json_data['member_of_campaign'] = campaign.get_prepid()
        json_data['step'] = campaign.get('step')
        new_request = Request(json_input=json_data)
        input_dataset = new_request.get('input_dataset')
        input_dataset_parts = [x for x in input_dataset.split('/') if x]
        era = input_dataset_parts[1].split('-')[0]
        processing_string = new_request.get('processing_string')
        prepid_middle_part = f'{era}-{input_dataset_parts[0]}-{processing_string}'
        with self.locker.get_lock(f'generate-prepid-{campaign_name}'):
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
                new_request.set('sequences', campaign.get('sequences'))
            if not json_data.get('memory'):
                new_request.set('memory', campaign.get('memory'))

            if not json_data.get('energy'):
                new_request.set('energy', campaign.get('energy'))

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
        campaign_tickets_db = Database('campaign_tickets')
        campaign_tickets = campaign_tickets_db.query(f'created_requests={prepid}')
        self.logger.debug(json.dumps(campaign_tickets, indent=4))
        for campaign_ticket_json in campaign_tickets:
            campaign_ticket = CampaignTicket(json_input=campaign_ticket_json)
            campaign_ticket.set('created_requests', [x for x in campaign_ticket.get('created_requests') if x != prepid])
            campaign_ticket.add_history('remove_request', prepid, None)
            campaign_tickets_db.save(campaign_ticket.get_json())

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
        editing_info['member_of_campaign'] = is_new
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
