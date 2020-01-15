from core.controller.controller_base import ControllerBase
from core.model.request import Request
from core.model.campaign import Campaign
from core.database.database import Database


class RequestController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'requests'
        self.model_class = Request

    def create(self, json_data):
        """
        Create a new request from given json_data
        """
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
            serial_numbers = request_db.query_view('serial_number', f'key="{campaign_name}"&group=true')
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

            if self.check_for_create(new_request):
                if not request_db.save(new_request.json()):
                    raise Exception(f'Error saving {prepid}')

                return new_request.json()
            else:
                self.logger.error('Error while checking new item %s', prepid)
                return None

    def check_for_create(self, obj):
        """
        Perform checks on object before adding it to database
        """
        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        """
        Compare existing and updated objects to see if update is valid
        """
        return True

    def check_for_delete(self, obj):
        """
        Perform checks on object before deleting it from database
        """
        return True

    def get_editing_info(self, request):
        editing_info = {k: not k.startswith('_') for k in request.json().keys()}
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
        return editing_info
