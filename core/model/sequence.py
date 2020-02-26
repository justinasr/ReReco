"""
Module that contains Sequence class
"""
import weakref
from core.model.model_base import ModelBase


class Sequence(ModelBase):
    """
    Sequence is a dictionary that has all user editable attributes
    for cmsDriver command
    """

    _ModelBase__schema = {
        # What conditions to use. This has to be specified
        'conditions': '',
        # Hash of configuration file uploaded to ReqMgr2
        'config_id': '',
        # Specify the file where the code to modify the process object is stored
        # If inline_custom is set to 1, then inline the customisation file
        'customise': '',
        # What data tier to use
        'datatier': [],
        # Specify which era to use (e.g. "run2")
        'era': '',
        # What event content to write out
        'eventcontent': [],
        # Freeform attributes appended at the end
        'extra': '',
        # Hash of harvesting configuration file uploaded to ReqMgr2
        'harvesting_config_id': '',
        # How many threads should CMSSW use
        'nThreads': 1,
        # Scenario overriding standard settings: 'pp', 'cosmics', 'nocoll', 'HeavyIons'
        'scenario': 'pp',
        # The desired step. The possible values are:
        # RAW2DIGI, L1Reco, RECO, EI, PAT, NANO, ALCA[:@...], DQM[:@...], SKIM[:@...]
        'step': []}

    lambda_checks = {
        'conditions': lambda c: ModelBase.matches_regex(c, '[a-zA-Z0-9_]{0,50}'),
        'config_id': lambda cid: ModelBase.matches_regex(cid, '[a-f0-9]{0,50}'),
        '__datatier': lambda s: s in ('AOD', 'MINIAOD', 'NANOAOD', 'DQMIO', 'USER', 'ALCARECO'),
        'era': lambda e: ModelBase.matches_regex(e, '[a-zA-Z0-9_\\,]{0,50}'),
        '__eventcontent': lambda s: s in ('AOD', 'MINIAOD', 'NANOAOD', 'DQM', 'NANOEDMAOD'),
        'harvesting_config_id': lambda cid: ModelBase.matches_regex(cid, '[a-f0-9]{0,50}'),
        'nThreads': lambda n: 0 < n < 64,
        'scenario': lambda s: s in ('pp', 'cosmics', 'nocoll', 'HeavyIons'),
        '__step': lambda s: (s in ('RAW2DIGI', 'L1Reco', 'RECO', 'EI', 'PAT', 'NANO') or
                             s.startswith('ALCA') or
                             s.startswith('DQM') or
                             s.startswith('SKIM'))
    }

    def __init__(self, json_input=None, parent=None):
        ModelBase.__init__(self, json_input)
        if parent:
            self.parent = weakref.ref(parent)
        else:
            self.parent = None

    def get_prepid(self):
        parent = self.parent()
        index = self.get_index_in_parent()
        return f'Sequence_{parent}_{index}'

    def needs_harvesting(self):
        """
        Return if this sequence produces input file for harvesting
        and harvesting step is needed
        """
        for step in self.get('step'):
            if step == 'DQM' or step.startswith('DQM:'):
                return True

        return False

    def get_index_in_parent(self):
        for index, sequence in enumerate(self.parent().get('sequences')):
            if self == sequence:
                return index

        raise Exception(f'Sequence is not a child of {self.parent().get_prepid()}')

    def get_name(self):
        """
        Return a sequence name which is based on parent
        prepid and sequence number
        Last sequence always has the same name as parent prepid
        Other sequences have suffix with their index, e.g

        PrepID_0
        PrepID_1
        PrepID

        If there is only one sequence, it will be the last one
        and have the same name as parent prepid
        """
        index = self.get_index_in_parent()
        parent_prepid = self.parent().get_prepid()
        if index != len(self.parent().get('sequences')) - 1:
            index = f'{parent_prepid}_{index}'
        else:
            sequence_name = f'{parent_prepid}'

        return sequence_name

    def get_config_file_names(self):
        parent_prepid = self.parent().get_prepid()
        index = self.get_index_in_parent()
        config_file_names = {'config': f'{parent_prepid}_{index}_cfg'}
        if self.needs_harvesting():
            config_file_names['harvest'] = f'{parent_prepid}_{index}_harvest_cfg'

        return config_file_names

    def __build_cmsdriver(self, cmsdriver_type, arguments):
        """
        Build a cmsDriver command from given arguments
        Add comment in front of the command
        """
        # Actual command
        command = f'# Command for {cmsdriver_type}:\ncmsDriver.py {cmsdriver_type}'
        # Comment in front of the command for better readability
        comment = f'# Arguments for {cmsdriver_type}:\n'
        for key in sorted(arguments.keys()):
            if not arguments[key]:
                continue

            if key in ('extra'):
                continue

            if isinstance(arguments[key], bool):
                arguments[key] = ''

            if isinstance(arguments[key], list):
                arguments[key] = ','.join([str(x) for x in arguments[key]])

            command += f' --{key} {arguments[key]}'.rstrip()
            comment += f'# --{key} {arguments[key]}'.rstrip() + '\n'

        if arguments.get('extra'):
            extra_value = arguments['extra']
            command += f' {extra_value}'
            comment += f'# <extra> {extra_value}\n'

        return comment + '\n' + command

    def get_cmsdriver(self, overwrite_input=None):
        """
        Return a cmsDriver command for this sequence
        Config file is named like this
        PrepID_0_cfg.py
        """
        arguments_dict = dict(self.get_json())
        # Delete sequence metadata
        if 'config_id' in arguments_dict:
            del arguments_dict['config_id']

        if 'harvesting_config_id' in arguments_dict:
            del arguments_dict['harvesting_config_id']

        # Handle input/output file names
        if overwrite_input:
            arguments_dict['filein'] = overwrite_input
        else:
            index = self.get_index_in_parent()
            if index == 0:
                input_dataset = self.parent().get('input_dataset')
                arguments_dict['filein'] = f'"dbs:{input_dataset}"'
            else:
                previous_sequence = self.parent().get('sequences')[index - 1]
                input_file = f'{previous_sequence.get_name()}.root'
                arguments_dict['filein'] = f'"file:{input_file}"'

        # Build argument dictionary
        sequence_name = self.get_name()
        config_names = self.get_config_file_names()
        arguments_dict['fileout'] = f'"file:{sequence_name}.root"'
        arguments_dict['python_filename'] = f'"{config_names["config"]}.py"'
        arguments_dict['data'] = True
        arguments_dict['no_exec'] = True
        cms_driver_command = self.__build_cmsdriver('RECO', arguments_dict)
        return cms_driver_command

    def get_harvesting_cmsdriver(self):
        """
        Return a harvesting cmsDriver for this sequence
        Config file is named like this
        PrepID_0_harvest_cfg.py
        """
        if not self.needs_harvesting():
            return ''

        arguments_dict = dict(self.get_json())
        # Delete sequence metadata
        if 'config_id' in arguments_dict:
            del arguments_dict['config_id']

        if 'harvesting_config_id' in arguments_dict:
            del arguments_dict['harvesting_config_id']
        # Get correct configuration of DQM step, e.g.
        # DQM:@rerecoCommon should be changed to HARVESTING:@rerecoCommon
        step = 'HARVESTING'
        for one_step in self.get('step'):
            if one_step.startswith('DQM:'):
                step = one_step.replace('DQM:', 'HARVESTING:', 1)
                break

        # Build argument dictionary
        sequence_name = self.get_name()
        config_names = self.get_config_file_names()
        arguments_dict['step'] = step
        arguments_dict['era'] = arguments_dict['era'].split(',')[0]
        arguments_dict['filein'] = f'"file:{sequence_name}_inDQM.root"',
        arguments_dict['python_filename'] = f'"{config_names["harvest"]}.py"'
        harvesting_command = self.__build_cmsdriver('HARVESTING', arguments_dict)
        return harvesting_command
