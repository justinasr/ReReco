from core.model.model_base import ModelBase


class Request(ModelBase):

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
        # PrepID
        'prepid': '',
        # Energy in TeV
        'energy': 0.0,
        # Type LHE, MCReproc, Prod
        'type': '',
        # Step type: DR, MiniAOD, NanoAOD, etc.
        'step': 'DR',
        # CMSSW version
        'cmssw_version': '',
        # User notes
        'notes': '',
        # List of dictionaries that have cmsDriver options
        'sequences': [],
        # Action history
        'history': [],
        # Default memory
        'memory': 2300,
        # Status is either new or done
        'status': 'new',
        # Campaign
        'member_of_campaign': '',
        # Input dataset name
        'input_dataset': ''}

    __lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\-]{1,50}'),
        'energy': lambda energy: energy >= 0.0,
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'type': lambda step: step in ['Prod', 'MCReproc', 'LHE'],
        'memory': lambda memory: memory >= 0,
        'cmssw_version': lambda cmssw: ModelBase.matches_regex(cmssw, 'CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}'),  # CMSSW_ddd_ddd_ddd[_XXX...]
        'status': lambda status: status in ('new', 'approved', 'submitted', 'done')
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name in self.__lambda_checks:
            return self.__lambda_checks.get(attribute_name)(attribute_value)

        return True
