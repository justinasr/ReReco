"""
Module that contains Campaign class
"""
from core.model.model_base import ModelBase


class Campaign(ModelBase):
    """
    Class that represents a computing campaign
    It is used as a template for requests
    """

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
        # PrepID
        'prepid': '',
        # Energy in TeV
        'energy': 0.0,
        # Step type: DR, MiniAOD, NanoAOD, etc.
        'step': 'DR',
        # CMSSW version
        'cmssw_release': '',
        # User notes
        'notes': '',
        # List of dictionaries that have cmsDriver options
        'sequences': [],
        # Action history
        'history': [],
        # Default memory
        'memory': 2300
    }

    _lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9]{1,50}'),
        'energy': lambda energy: energy >= 0.0,
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'memory': lambda memory: memory >= 0,
        'cmssw_release': ModelBase._lambda_checks['cmssw_release']
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)
