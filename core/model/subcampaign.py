"""
Module that contains Subcampaign class
"""
from core.model.model_base import ModelBase


class Subcampaign(ModelBase):
    """
    Class that represents a snapshot computing campaign
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
        'memory': 2300,
        # Path to json that contains all runs
        'runs_json_path': ''
    }

    _lambda_checks = {
        'prepid': lambda prepid: ModelBase._lambda_checks['subcampaign'],
        'energy': lambda energy: energy >= 0.0,
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'memory': lambda memory: memory >= 0,
        'cmssw_release': ModelBase._lambda_checks['cmssw_release']
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def before_attribute_check(self, attribute_name, attribute_value):
        if attribute_name == 'runs_json_path':
            while attribute_value.startswith('/'):
                attribute_value = attribute_value[1:]

        return attribute_value
