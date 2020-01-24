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
        # List of workflows in computing
        'workflows': []
    }

    _lambda_checks = {
        'cmssw_release': lambda cmssw: ModelBase.matches_regex(cmssw, 'CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}'),  # CMSSW_ddd_ddd_ddd[_XXX...]
        'energy': lambda energy: energy >= 0.0,
        'input_dataset': ModelBase._lambda_checks['dataset'],
        'memory': lambda memory: memory >= 0,
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-_]{1,50}'),
        'priority': lambda priority: 1000 <= priority <= 1000000,
        'processing_string': ModelBase._lambda_checks['processing_string'],
        '__runs': lambda r: isinstance(r, int) and r > 0,
        'size_per_event': lambda spe: spe > 0.0,
        'status': lambda status: status in ('new', 'approved', 'submitted', 'done'),
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'time_per_event': lambda tpe: tpe > 0.0,
        'type': lambda step: step in ['Prod', 'MCReproc', 'LHE']
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def before_attribute_check(self, attribute_name, attribute_value):
        if attribute_name == 'runs':
            runs = []
            for run in attribute_value:
                if run not in runs:
                    runs.append(int(run))

            return runs

        return super().before_attribute_check(attribute_name, attribute_value)

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
        sequence_json = dict(sequence_json)
        prepid = self.get_prepid()
        if sequence_index == 0:
            input_dataset = self.get("input_dataset")
            sequence_json['filein'] = f'"dbs:{input_dataset}"'
        else:
            input_file = f'{prepid}_{sequence_index - 1}.root'
            sequence_json['filein'] = f'"file:{input_file}"'

        if sequence_index != len(self.get('sequences')) - 1:
            output_file = f'{prepid}_{sequence_index}.root'
            sequence_json['fileout'] = f'"file:{output_file}"'

        for datatier in sequence_json.get('datatier', []):
            if datatier.startswith('DQM'):
                step_type = 'HARVEST'
                break
        else:
            step_type = 'RECO'

        cms_driver_command = f'cmsDriver.py {step_type}'
        for key in sorted(sequence_json.keys()):
            if not sequence_json[key]:
                continue

            if isinstance(sequence_json[key], list):
                sequence_json[key] = ','.join([str(x) for x in sequence_json[key]])

            cms_driver_command += ' --%s %s' % (key, sequence_json[key])

        cms_driver_command += ' --no_exec'
        cms_driver_command += ' --data'
        python_filename = f'{step_type.lower()}_{prepid}_{sequence_index}_cfg.py'
        cms_driver_command += f' --python_filename="{python_filename}"'
        cms_driver_command += f'\ncmsRun {python_filename}'
        return cms_driver_command
