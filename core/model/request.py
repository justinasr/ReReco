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
        # Automatically add harvesting driver if sequence has DQM step
        'enable_harvesting': True,
        # Energy in TeV
        'energy': 0.0,
        # Action history
        'history': [],
        # Input dataset name or request name
        'input': {'dataset': '',
                  'request': ''},
        # Dictionary of runs and their lumisection ranges to be processed
        'lumisections': {},
        # Memory in MB
        'memory': 2000,
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
        'size_per_event': [],
        # Status is either new, approved, submitted or done
        'status': 'new',
        # Subcampaign name
        'subcampaign': '',
        # Time per event in seconds
        'time_per_event': [],
        # Total events
        'total_events': 0,
        # List of workflows in computing
        'workflows': []
    }

    lambda_checks = {
        'prepid': ModelBase.request_id_check,
        'cmssw_release': ModelBase.cmssw_check,
        'completed_events': lambda events: events >= 0,
        'energy': ModelBase.lambda_check('energy'),
        '_input': {'dataset': lambda ds: not ds or ModelBase.dataset_check(ds),
                   'request': lambda r:
                              not r
                              or ModelBase.request_id_check(r)},
        'memory': ModelBase.lambda_check('memory'),
        '__output_datasets': ModelBase.dataset_check,
        'priority': ModelBase.lambda_check('priority'),
        'processing_string': ModelBase.processing_string_check,
        '__runs': lambda r: isinstance(r, int) and r > 0,
        '__sequences': lambda s: isinstance(s, Sequence),
        '__size_per_event': lambda spe: spe > 0.0,
        'status': lambda status: status in {'new', 'approved', 'submitting', 'submitted', 'done'},
        'subcampaign': ModelBase.subcampaign_id_check,
        '__time_per_event': lambda tpe: tpe > 0.0,
        'total_events': lambda events: events >= 0,
    }

    def __init__(self, json_input=None, check_attributes=True):
        if json_input:
            json_input = deepcopy(json_input)
            json_input['runs'] = [int(r) for r in json_input.get('runs', [])]
            sequence_objects = []
            for sequence_json in json_input.get('sequences', []):
                sequence_objects.append(Sequence(json_input=sequence_json,
                                                 parent=self,
                                                 check_attributes=check_attributes))

            json_input['sequences'] = sequence_objects

        ModelBase.__init__(self, json_input, check_attributes)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name == 'input':
            if not attribute_value.get('dataset') and not attribute_value.get('request'):
                raise Exception('Either input dataset or input request must be provided')

        return super().check_attribute(attribute_name, attribute_value)

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
        input_dataset_parts = [x for x in self.get('input')['dataset'].split('/') if x]
        if len(input_dataset_parts) < 2:
            return self.get_prepid().split('-')[1]

        return input_dataset_parts[1].split('-')[0]

    def get_input_processing_string(self):
        """
        Return processing string from input dataset
        """
        input_dataset_parts = [x for x in self.get('input')['dataset'].split('/') if x]
        if len(input_dataset_parts) < 3:
            return ''

        middle_parts = [x for x in input_dataset_parts[1].split('-') if x]
        if len(middle_parts) < 3:
            return ''

        return '-'.join(middle_parts[1:-1])

    def get_dataset(self):
        """
        Return primary dataset based on input dataset
        """
        input_dataset_parts = [x for x in self.get('input')['dataset'].split('/') if x]
        if not input_dataset_parts:
            return self.get_prepid().split('-')[2]

        return input_dataset_parts[0]

    def get_request_string(self):
        """
        Return request string made of era, dataset and processing string
        """
        processing_string = self.get('processing_string')
        era = self.get_era()
        dataset = self.get_dataset()
        return f'{era}_{dataset}_{processing_string}'.strip('_')

    def get_datatiers(self):
        """
        Return datatiers of all sequences
        """
        datatiers = []
        for sequence in self.get('sequences'):
            datatiers.extend(sequence.get('datatier'))

        return datatiers
