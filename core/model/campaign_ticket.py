from core.model.model_base import ModelBase


class CampaignTicket(ModelBase):

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
        # PrepID
        'prepid': '',
        # Name of campaign that was used as template for requests
        'campaign_name': '',
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
        'history': []}

    __lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9]{1,50}'),
        'campaign_name': lambda campaign_name: ModelBase.matches_regex(campaign_name, '[a-zA-Z0-9]{1,50}'),
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
                    raise Exception('Invalid input dataset name: %s' % (dataset))

        return True
