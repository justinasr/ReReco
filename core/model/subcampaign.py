"""
Module that contains Subcampaign class
"""
from core.model.model_base import ModelBase
from core.model.sequence import Sequence


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
        # CMSSW version
        'cmssw_release': '',
        # Energy in TeV
        'energy': 0.0,
        # Action history
        'history': [],
        # Default memory
        'memory': 2300,
        # User notes
        'notes': '',
        # Path to json that contains all runs
        'runs_json_path': '',
        # scram architecture
        'scram_arch': '',
        # List of Sequences
        'sequences': [],
        # Step type: DR, MiniAOD, NanoAOD, etc.
        'step': 'DR',
    }

    lambda_checks = {
        'prepid': ModelBase.lambda_check('subcampaign'),
        'cmssw_release': ModelBase.lambda_check('cmssw_release'),
        'energy': ModelBase.lambda_check('energy'),
        'memory': ModelBase.lambda_check('memory'),
        'runs_json_path': lambda rjp: ModelBase.matches_regex(rjp, '[a-zA-Z0-9/\\-_]{0,150}(\\.json|\\.txt)?'),
        'scram_arch': ModelBase.lambda_check('scram_arch'),
        '__sequences': lambda s: isinstance(s, Sequence),
        'step': ModelBase.lambda_check('step'),
    }

    def __init__(self, json_input=None):
        if json_input:
            json_input['runs_json_path'] = json_input.get('runs_json_path', '').strip().lstrip('/')
            sequence_objects = []
            for index, sequence_json in enumerate(json_input.get('sequences', [])):
                sequence_objects.append(Sequence(json_input=sequence_json))

            json_input['sequences'] = sequence_objects

        ModelBase.__init__(self, json_input)
