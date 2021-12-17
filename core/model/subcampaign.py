"""
Module that contains Subcampaign class
"""
from core.model.model_base import ModelBase
from core.model.sequence import Sequence


class Subcampaign(ModelBase):
    """
    Class that represents a snapshot of computing campaign
    It is used as a template for requests
    """

    _ModelBase__schema = {
        # Database id (required by DB)
        '_id': '',
        # PrepID
        'prepid': '',
        # CMSSW version
        'cmssw_release': '',
        # Automatically add harvesting driver if sequence has DQM step
        'enable_harvesting': True,
        # Energy in TeV
        'energy': 0.0,
        # Action history
        'history': [],
        # Default memory
        'memory': 2000,
        # User notes
        'notes': '',
        # Path to json that contains all runs
        'runs_json_path': '',
        # List of Sequences
        'sequences': [],
    }

    lambda_checks = {
        'prepid': ModelBase.subcampaign_id_check,
        'cmssw_release': ModelBase.cmssw_check,
        'energy': ModelBase.lambda_check('energy'),
        'memory': ModelBase.lambda_check('memory'),
        'runs_json_path': ModelBase.runs_json_path_check,
        'sequences': lambda s: len(s) > 0,
        '__sequences': lambda s: isinstance(s, Sequence),
    }

    def __init__(self, json_input=None, check_attributes=True):
        if json_input:
            json_input['runs_json_path'] = json_input.get('runs_json_path', '').strip().lstrip('/')
            sequence_objects = []
            for sequence_json in json_input.get('sequences', []):
                sequence_objects.append(Sequence(json_input=sequence_json))

            json_input['sequences'] = sequence_objects

        ModelBase.__init__(self, json_input, check_attributes)
