"""
Module that contains Request class
"""
from core.model.model_base import ModelBase
from core.model.sequence import Sequence


class Request(ModelBase):
    """
    Request represents a single step in processing pipeline
    Request contains one or a few cmsDriver commands
    It is created based on a subcampaign that it is a member of
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
        # Subcampaign name
        'subcampaign': '',
        # Time per event in seconds
        'time_per_event': 1.0,
        # List of workflows in computing
        'workflows': []
    }

    _lambda_checks = {
        'cmssw_release': lambda cmssw: ModelBase._lambda_checks['cmssw_release'],
        'energy': lambda energy: energy >= 0.0,
        'input_dataset': ModelBase._lambda_checks['dataset'],
        'memory': lambda memory: memory >= 0,
        'prepid': lambda prepid: ModelBase.matches_regex(prepid, '[a-zA-Z0-9\\-_]{1,100}'),
        'priority': lambda priority: 1000 <= priority <= 1000000,
        'processing_string': ModelBase._lambda_checks['processing_string'],
        '__runs': lambda r: isinstance(r, int) and r > 0,
        '__sequences': lambda s: isinstance(s, Sequence),
        'size_per_event': lambda spe: spe > 0.0,
        'status': lambda status: status in ('new', 'approved', 'submitting', 'submitted', 'done'),
        'step': lambda step: step in ['DR', 'MiniAOD', 'NanoAOD'],
        'subcampaign': lambda subcampaign: ModelBase._lambda_checks['subcampaign'],
        'time_per_event': lambda tpe: tpe > 0.0,
        'type': lambda step: step in ['Prod', 'MCReproc', 'LHE']
    }

    def __init__(self, json_input=None):
        json_input['runs'] = [int(r) for r in json_input.get('runs', [])]
        json_input['sequences'] = [Sequence(json_input=s) for s in json_input.get('sequences', [])]
        ModelBase.__init__(self, json_input)

    def get_cmssw_setup(self):
        """
        Return code needed to set up CMSSW environment
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

    def get_sequence_name(self, sequence_index):
        """
        Return a sequence name which is based on request
        prepid and sequence number
        Last sequence always has the same name as prepid
        Other sequences have suffix with their index, e.g

        PrepID_0
        PrepID_1
        PrepID

        If there is only one sequence, it will be the last one
        and have the same name as prepid
        """
        prepid = self.get_prepid()
        if sequence_index != len(self.get('sequences')) - 1:
            sequence_name = f'{prepid}_{sequence_index}'
        else:
            sequence_name = f'{prepid}'

        return sequence_name

    def build_cmsdriver(self, cmsdriver_type, arguments):
        """
        Build a cmsDriver command from given arguments
        """
        # Actual command
        command = f'# Command for {cmsdriver_type}:\ncmsDriver.py {cmsdriver_type}'
        # Comment in front of the command for better readability
        comment = f'# Arguments for {cmsdriver_type}:\n'
        for key in sorted(arguments.keys()):
            if not arguments[key]:
                continue

            if isinstance(arguments[key], bool):
                arguments[key] = ''

            if isinstance(arguments[key], list):
                arguments[key] = ','.join([str(x) for x in arguments[key]])

            command += f' --{key} {arguments[key]}'.rstrip()
            comment += f'# --{key} {arguments[key]}'.rstrip() + '\n'

        self.logger.debug(command)
        return comment + '\n' + command

    def get_cmsdriver(self, sequence_index, overwrite_input=None):
        """
        Return a cmsDriver command for sequence at given index
        Config files are named like this
        PrepID_0_cfg.py for normal config
        PrepID_0_harvesting_cfg.py for harvesting
        All python files have prepid and sequence number
        """
        prepid = self.get_prepid()
        sequence = self.get('sequences')[sequence_index]
        arguments_dict = dict(sequence.get_json())
        # Delete sequence metadata
        if 'config_id' in arguments_dict:
            del arguments_dict['config_id']

        if 'harvesting_config_id' in arguments_dict:
            del arguments_dict['harvesting_config_id']

        # Handle input/output file names
        if overwrite_input:
            arguments_dict['filein'] = overwrite_input
        else:
            if sequence_index == 0:
                input_dataset = self.get("input_dataset")
                arguments_dict['filein'] = f'"dbs:{input_dataset}"'
            else:
                input_file = f'{self.get_sequence_name(sequence_index - 1)}.root'
                arguments_dict['filein'] = f'"file:{input_file}"'

        # Build argument dictionary
        sequence_name = self.get_sequence_name(sequence_index)
        python_filename = f'{prepid}_{sequence_index}'
        arguments_dict['fileout'] = f'"file:{sequence_name}.root"'
        arguments_dict['python_filename'] = f'"{python_filename}_cfg.py"'
        arguments_dict['data'] = True
        arguments_dict['no_exec'] = True
        arguments_dict['runUnscheduled'] = True

        cms_driver_command = self.build_cmsdriver('RECO', arguments_dict)

        # Add harvesting if needed
        needs_harvest = sequence.needs_harvesting()
        if needs_harvest:
            # Get correct configuration of DQM step, e.g.
            # DQM:@rerecoCommon should be changed to HARVESTING:@rerecoCommon
            for one_step in sequence.get('step'):
                if one_step == 'DQM':
                    step = 'HARVESTING'
                    break
                elif one_step.startswith('DQM:'):
                    step = one_step.replace('DQM:', 'HARVESTING:', 1)
                    break

            harvesting_dict = {'conditions': arguments_dict['conditions'],
                               'step': step,
                               'era': arguments_dict['era'].split(',')[0],
                               'scenario': arguments_dict['scenario'],
                               'data': True,
                               'no_exec': True,
                               'filein': f'"file:{sequence_name}_inDQM.root"',
                               'python_filename': f'"{python_filename}_harvest_cfg.py"'}
            cms_driver_command += '\n\n' + self.build_cmsdriver('HARVESTING', harvesting_dict)

        return cms_driver_command
