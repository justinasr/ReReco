"""
Module that contains Request class
"""
from copy import deepcopy
from core.model.model_base import ModelBase
from core.model.sequence import Sequence


class Request(ModelBase):
    """
    Request represents a single step in processing pipeline
    Request contains one or a few cmsDriver commands
    It is created based on a subcampaign that it is a member of
    """

    _ModelBase__schema = {
        # Database id (required by DB)
        '_id': '',
        # PrepID
        'prepid': '',
        # CMSSW version
        'cmssw_release': '',
        # Completed events
        'completed_events': 0,
        # Energy in TeV
        'energy': 0.0,
        # Action history
        'history': [],
        # Input dataset name
        'input_dataset': '',
        # Memory in MB
        'memory': 2300,
        # User notes
        'notes': '',
        # List of output
        'output_datasets': [],
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
        # Subcampaign name
        'subcampaign': '',
        # Time per event in seconds
        'time_per_event': 1.0,
        # Total events
        'total_events': 0,
        # List of workflows in computing
        'workflows': []
    }

    lambda_checks = {
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-_]{1,100}'),
        'cmssw_release': ModelBase.lambda_check('cmssw_release'),
        'completed_events': lambda ce: ce >= 0,
        'energy': ModelBase.lambda_check('energy'),
        'input_dataset': lambda ds: not ds or ModelBase.lambda_check('dataset')(ds),
        'memory': ModelBase.lambda_check('memory'),
        '__output_datasets': ModelBase.lambda_check('dataset'),
        'priority': lambda priority: 1000 <= priority <= 1000000,
        'processing_string': ModelBase.lambda_check('processing_string'),
        '__runs': lambda r: isinstance(r, int) and r > 0,
        '__sequences': lambda s: isinstance(s, Sequence),
        'size_per_event': lambda spe: spe > 0.0,
        'status': lambda status: status in ('new', 'approved', 'submitting', 'submitted', 'done'),
        'step': ModelBase.lambda_check('step'),
        'subcampaign': ModelBase.lambda_check('subcampaign'),
        'time_per_event': lambda tpe: tpe > 0.0,
        'total_events': lambda te: te >= 0,
        'type': lambda step: step in ['Prod', 'MCReproc', 'LHE'],
    }

    def __init__(self, json_input=None):
        if json_input:
            json_input = deepcopy(json_input)
            json_input['runs'] = [int(r) for r in json_input.get('runs', [])]
            sequence_objects = []
            for sequence_json in json_input.get('sequences', []):
                sequence_objects.append(Sequence(json_input=sequence_json, parent=self))

            json_input['sequences'] = sequence_objects

        ModelBase.__init__(self, json_input)

    def get_cmssw_setup(self):
        """
        Return code needed to set up CMSSW environment for this request
        Basically, cmsenv command
        """
        cmssw_release = self.get('cmssw_release')
        commands = [f'source /cvmfs/cms.cern.ch/cmsset_default.sh',
                    f'if [ -r {cmssw_release}/src ] ; then',
                    f'  echo {cmssw_release} already exist',
                    f'else',
                    f'  scram p CMSSW {cmssw_release}',
                    f'fi',
                    f'cd {cmssw_release}/src',
                    f'eval `scram runtime -sh`',
                    f'cd ../..']

        return '\n'.join(commands)

    def get_config_file_names(self):
        """
        Get list of dictionaries of all config file names without extensions
        """
        file_names = []
        for sequence in self.get('sequences'):
            file_names.append(sequence.get_config_file_names())

        return file_names

    def get_cmsdrivers(self, overwrite_input=None):
        """
        Get all cmsDriver commands for this request
        """
        built_command = ''
        for index, sequence in enumerate(self.get('sequences')):
            if index == 0 and overwrite_input:
                built_command += sequence.get_cmsdriver(overwrite_input)
            else:
                built_command += sequence.get_cmsdriver()

            if sequence.needs_harvesting():
                built_command += '\n\n'
                built_command += sequence.get_harvesting_cmsdriver()

            built_command += '\n\n'

        return built_command.strip()

    def get_era(self):
        """
        Return era based on input dataset
        """
        input_dataset_parts = [x for x in self.get('input_dataset').split('/') if x]
        return input_dataset_parts[1].split('-')[0]

    def get_dataset(self):
        """
        Return primary dataset based on input dataset
        """
        input_dataset_parts = [x for x in self.get('input_dataset').split('/') if x]
        return input_dataset_parts[0]
