"""
Module that contains a Flow class
"""
from core.model.model_base import ModelBase


class Flow(ModelBase):
    """
    Flow is used to join two requests (campaigns) in a chained campaign
    """

    _ModelBase__schema = {
        # Database id
        '_id': '',
        # Document revision
        '_rev': '',
        # PrepID
        'prepid': '',
        # List of allowed source campaigns prepids
        'source_campaigns': [],
        # Target campaign prepid
        'target_campaign': ''}

    lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9]{1,50}')
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)
        self.collection = 'flows'
