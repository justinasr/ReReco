"""
Module that contains Ticket class
"""
from copy import deepcopy
from core.model.model_base import ModelBase


class Ticket(ModelBase):
    """
    Ticket has a list of input datasets and a list of steps specifications
    Ticket can be used to create requests each input dataset
    """

    _ModelBase__schema = {
        # Database id (required by DB)
        '_id': '',
        # PrepID
        'prepid': '',
        # List of prepids of requests that were created from this ticket
        'created_requests': [],
        # Action history
        'history': [],
        # List of input dataset names
        'input_datasets': [],
        # User notes
        'notes': '',
        # Status is either new or done
        'status': 'new',
        # List of dicts that have subcampaign, processing_string, size/time per event values
        'steps': [],
    }

    lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9_\\-]{1,75}'),
        '__created_requests': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-_]{1,100}'),
        '__input_datasets': ModelBase.lambda_check('dataset'),
        'status': lambda status: status in {'new', 'done'},
        'steps': lambda s: len(s) > 0,
    }

    def __init__(self, json_input=None):
        if json_input:
            json_input = deepcopy(json_input)
            steps = []
            for step in json_input.get('steps', []):
                steps.append({'subcampaign': step.get('subcampaign', ''),
                              'processing_string': step.get('processing_string', ''),
                              'time_per_event': float(step.get('time_per_event', 0)),
                              'size_per_event': float(step.get('size_per_event', 0)),
                              'priority': int(step.get('priority', 0))})

            json_input['steps'] = steps

        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name == 'steps':
            if not isinstance(attribute_value, list):
                raise Exception(f'Expected {attribute_name} to be a list')

            for step in attribute_value:
                subcampaign = step['subcampaign']
                if not ModelBase.lambda_check('subcampaign')(subcampaign):
                    raise Exception(f'Bad subcampaign prepid {subcampaign}')

                processing_string = step['processing_string']
                if not ModelBase.lambda_check('processing_string')(processing_string):
                    raise Exception(f'Bad processing string {processing_string}')

                time_per_event = step['time_per_event']
                if time_per_event <= 0.0:
                    raise Exception(f'Bad time per event {time_per_event}')

                size_per_event = step['size_per_event']
                if size_per_event <= 0.0:
                    raise Exception(f'Bad size per event {size_per_event}')

                priority = step['priority']
                if not ModelBase.lambda_check('priority')(priority):
                    raise Exception(f'Bad priority {priority}')

        return super().check_attribute(attribute_name, attribute_value)
