"""
Module that contains ChainedRequestController class
"""
from core.database.database import Database
from core.model.chained_request import ChainedRequest
from core.controller.controller_base import ControllerBase


class ChainedRequestController(ControllerBase):
    """
    Controller that has all actions related to a subcampaign
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'chained_requests'
        self.model_class = ChainedRequest

    def create(self, json_data):
        # Clean up the input
        chained_request_db = Database(self.database_name)
        json_data['prepid'] = 'Temp00001'
        chained_request = ChainedRequest(json_input=json_data)
        # Use first subcampaign name for prepid
        subcampaign_names = []
        request_controller = self.get_request_controller()
        for step in chained_request.get('requests'):
            request = request_controller.get(step['request'])
            subcampaign_names.append(request.get('subcampaign'))
            subcampaign_names.append(request.get('processing_string'))

        prepid_middle_part = '_'.join(subcampaign_names)
        with self.locker.get_lock(f'generate-chained-request-prepid-{prepid_middle_part}'):
            # Get a new serial number
            serial_numbers = chained_request_db.query(f'prepid={prepid_middle_part}-*',
                                                      limit=1,
                                                      sort_asc=False)
            if not serial_numbers:
                serial_number = 0
            else:
                serial_number = serial_numbers[0]['prepid']
                serial_number = int(serial_number.split('-')[-1])

            serial_number += 1
            # Form a new temporary prepid
            prepid = f'{prepid_middle_part}-{serial_number:05d}'
            json_data['prepid'] = prepid
            return super().create(json_data)

    def check_for_delete(self, obj):
        request_controller = self.get_request_controller()
        for step in obj.get('requests'):
            request = request_controller.get(step['request'])
            if request.get('status') != 'new':
                raise Exception('All requests must be in status "new" before chaiend request can be deleted')

        return True

    def before_delete(self, obj):
        request_controller = self.get_request_controller()
        for step in reversed(obj.get('requests')):
            request_controller.delete({'prepid': step['request']})

        return True

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        new = not bool(prepid)
        editing_info['prepid'] = new

        return editing_info

    def get_request_controller(self):
        from core.controller.request_controller import RequestController
        return RequestController()