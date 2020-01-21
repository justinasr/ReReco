"""
Module that contains Request class
"""
from core.model.model_base import ModelBase


class Request(ModelBase):
    """
    Request represents a single step in processing pipeline
    Request contains one or a few cmsDriver commands
    It is created based on a campaign that it is a member of
    """

    _ModelBase__schema = {
        # Database id (required by CouchDB)
        '_id': '',
        # Document revision (required by CouchDB)
        '_rev': '',
        # CMSSW version
        'cmssw_release': '',
        # Energy in TeV
        'energy': 0.0,
        # Action history
        'history': [],
        # Input dataset name
        'input_dataset': '',
        # Campaign name
        'member_of_campaign': '',
        # Memory in MB
        'memory': 2300,
        # User notes
        'notes': '',
        # List of output
        'output_datasets': [],
        # PrepID
        'prepid': '',
        # Priority in computing
        'priority': 110000,
        # Processing string
        'processing_string': '',
        # List of runs to be processed
        'runs': [],
        # List of dictionaries that have cmsDriver options
        'sequences': [],
        # Disk size per event in kB
        'size_per_event': 1.0,
        # Status is either new, approved, submitted or done
        'status': 'new',
        # Step type: DR, MiniAOD, NanoAOD, etc.
        'step': 'DR',
        # Time per event in seconds
        'time_per_event': 1.0,
        # Type LHE, MCReproc, Prod
        'type': '',
        # List of workflows in computing
        'workflows': []
    }

    __lambda_checks = {
        'cmssw_release': lambda cmssw: ModelBase.matches_regex(cmssw, 'CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}'),  # CMSSW_ddd_ddd_ddd[_XXX...]
        'energy': lambda energy: energy >= 0.0,
        'memory': lambda memory: memory >= 0,
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-]{1,50}'),
        'priority': lambda priority: 1000 <= priority <= 1000000,
        'processing_string': lambda ps: ModelBase.matches_regex(ps, '[a-zA-Z0-9_]{0,100}'),
        'size_per_event': lambda spe: spe > 0.0,
        'status': lambda status: status in ('new', 'approved', 'submitted', 'done'),
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'time_per_event': lambda tpe: tpe > 0.0,
        'type': lambda step: step in ['Prod', 'MCReproc', 'LHE']
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name in self.__lambda_checks:
            return self.__lambda_checks.get(attribute_name)(attribute_value)

        return True

    def get_cmssw_setup(self):
        """
        Return code needed to set up CMSSW environment
        Basically, cmsenv command
        """
        cmssw_release = self.get('cmssw_release')
        commands = ['if [ -r %s/src ] ; then' % (cmssw_release),
                    '  echo release %s already exists' % (cmssw_release),
                    'else',
                    '  scram p CMSSW %s' % (cmssw_release),
                    'fi',
                    'cd %s/src' % (cmssw_release),
                    'eval `scram runtime -sh`']

        return '\n'.join(commands)

    def get_cmsdriver(self, sequence_index):
        """
        Return a build cmsDriver command for given sequence
        """
        sequence_json = self.get('sequences')[sequence_index]
        cms_driver_command = 'cmsDriver.py'
        for key, value in sequence_json.items():
            if not value:
                continue

            if isinstance(value, list):
                value = ','.join([str(x) for x in value])

            cms_driver_command += ' -%s %s' % (key, value)

        return cms_driver_command
