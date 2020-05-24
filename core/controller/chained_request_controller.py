"""
Module that contains ChainedRequestController class
"""
from core.database.database import Database
from core.controller.controller_base import ControllerBase
from core.controller.request_controller import RequestController
from core.model.chained_request import ChainedRequest


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
        request_controller = RequestController()
        for request_prepid in chained_request.get('requests'):
            request = request_controller.get(request_prepid)
            subcampaign_names.append(request.get('subcampaign'))

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

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        new = not bool(prepid)
        editing_info['prepid'] = new

        return editing_info
