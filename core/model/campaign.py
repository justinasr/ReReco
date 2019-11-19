from core.model.model_base import ModelBase


class Campaign(ModelBase):

    _ModelBase__schema = {
        # Database id
        '_id': '',
        # Document revision
        '_rev': '',
        # PrepID
        'prepid': '',
        # Energy in TeV
        'energy': 0.0,
        # Type LHE, MCReproc, Prod
        'type': '',
        # Step type: pLHE, wmLHEGS, GEN, GS, DR, MiniAOD, NanoAOD, etc.
        'step': 'pLHE',
        # CMSSW version
        'cmssw_release': '',
        # User notes
        'notes': '',
        # Campaign is root campaign of the chain, i.e. is the first in chain
        'is_root': True,
        # List of dictionaries that have cmsDriver options
        'sequences': [],
        # Action history
        'history': [],
        # Default memory
        'memory': 2300}

    __lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9]{1,50}'),
        'energy': lambda energy: energy >= 0.0,
        'step': lambda step: step in ['pLHE', 'wmLHEGS', 'GEN', 'GS', 'DR', 'MiniAOD', 'NanoAOD'],
        'memory': lambda memory: memory >= 0,
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name in self.__lambda_checks:
            return self.__lambda_checks.get(attribute_name)(attribute_value)

        return True
