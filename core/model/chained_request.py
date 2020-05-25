"""
Module that contains ChainedRequest class
"""
from copy import deepcopy
from core.model.model_base import ModelBase


class ChainedRequest(ModelBase):
    """
    ChainedRequest represents a list of subsequent steps
    ChainedRequest contains one or few Requests
    """

    _ModelBase__schema = {
        # Database id (required by DB)
        '_id': '',
        # PrepID
        'prepid': '',
        # Action history
        'history': [],
        # User notes
        'notes': '',
        # List of dicts that have prepids and join types
        'requests': []
    }

    lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-_]{1,100}'),
        'requests': lambda r: len(r) > 0,
        '__requests': lambda pair: isinstance(pair, dict) and ModelBase.matches_regex(pair['request'], '[a-zA-Z0-9\\-_]{1,100}') and ('join_type' not in pair or pair['join_type'] in ('on_done', 'together')),
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)
