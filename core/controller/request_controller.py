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

        with self.locker.get_lock(f'generate-prepid-{campaign_name}'):
            # Get a new serial number
            serial_numbers = request_db.query_view('serial_number',
                                                   f'key="{campaign_name}"&group=true')
            if not serial_numbers:
                serial_number = 0
            else:
                serial_number = serial_numbers[0]['value']

            serial_number += 1
            # Form a new prepid
            prepid = f'{campaign_name}-{serial_number:05d}'
            json_data['prepid'] = prepid
            # Finally create a request object
            new_request = Request(json_input=json_data)
            self.logger.info('Will create %s', (prepid))
            new_request.add_history('create', prepid, None)
            attributes_to_move = {'prepid': 'member_of_campaign',
                                  'memory': 'memory',
                                  'energy': 'energy',
                                  'step': 'step',
                                  'cmssw_release': 'cmssw_release',
                                  'type': 'type',
                                  'sequences': 'sequences'}
            for campaign_attr, request_attr in attributes_to_move.items():
                new_request.set(request_attr, campaign.get(campaign_attr))

            if 'input_dataset' in json_data:
                new_request.set('input_dataset', json_data['input_dataset'])

            if not self.check_for_create(new_request):
                self.logger.error('Error while checking new item %s', prepid)
                return None

            if not request_db.save(new_request.get_json()):
                raise Exception(f'Error saving {prepid}')

            return new_request.get_json()

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
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
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
            cms_driver += '\n'

        return cms_driver
