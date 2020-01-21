"""
Module that contains CampaignTicket class
"""
from core.model.model_base import ModelBase


class CampaignTicket(ModelBase):
    """
    Campaign ticket has a list of input datasets, a campaign and a processing string
    Campaign ticket can be used to create requests for each input dataset
    """

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
        # PrepID
        'prepid': '',
        # Name of campaign that is used as template for requests
        'campaign': '',
        # List of input dataset names
        'input_datasets': [],
        # Processing string for this ticket
        'processing_string': '',
        # List of prepids of requests that were created from this ticket
        'created_requests': [],
        # Status is either new or done
        'status': 'new',
        # User notes
        'notes': '',
        # Action history
        'history': []
    }

    __lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9]{1,50}'),
        'campaign': lambda campaign: ModelBase.matches_regex(campaign, '[a-zA-Z0-9]{1,50}'),
        'processing_string': lambda ps: ModelBase.matches_regex(ps, '[a-zA-Z0-9_]{0,100}'),
        'status': lambda status: status in ('new', 'done'),
        '__input_dataset': lambda ds: ModelBase.matches_regex(ds, '^/[a-zA-Z0-9\\-_]{1,99}/[a-zA-Z0-9\\.\\-_]{1,199}/[A-Z\\-]{1,50}$'),
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name in self.__lambda_checks:
            return self.__lambda_checks.get(attribute_name)(attribute_value)

        if attribute_name == 'input_datasets':
            for dataset in attribute_value:
                if not self.__lambda_checks.get('__input_dataset')(dataset):
                    raise Exception(f'Invalid input dataset name: {dataset}')

        return True
