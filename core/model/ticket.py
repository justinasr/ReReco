"""
Module that contains Ticket class
"""
from core.model.model_base import ModelBase


class Ticket(ModelBase):
    """
    Ticket has a list of input datasets and a list of steps specifications
    Ticket can be used to create requests or chains for each input dataset
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
        '__input_datasets': ModelBase.lambda_check('dataset'),
        'status': lambda status: status in ('new', 'done'),
        'steps': lambda s: len(s) > 0,
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)
