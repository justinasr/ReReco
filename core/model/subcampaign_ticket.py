"""
Module that contains CampaignTicket class
"""
from core.model.model_base import ModelBase


class SubcampaignTicket(ModelBase):
    """
    Subcampaign ticket has a list of input datasets, a subcampaign and a processing string
    Subcampaign ticket can be used to create requests for each input dataset
    """

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
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
        # Processing string for this ticket
        'processing_string': '',
        # Status is either new or done
        'status': 'new',
        # Name of subcampaign that is used as template for requests
        'subcampaign': ''
    }

    lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9_\\-]{1,75}'),
        '__input_datasets': ModelBase.lambda_check('dataset'),
        'processing_string': ModelBase.lambda_check('processing_string'),
        'status': lambda status: status in ('new', 'done'),
        'subcampaign': ModelBase.lambda_check('subcampaign'),
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)
