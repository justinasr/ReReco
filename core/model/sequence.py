"""
Module that contains Sequence class
"""
from core.model.model_base import ModelBase


class Sequence(ModelBase):
    """
    Sequence is a dictionary that has all user editable attributes
    for cmsDriver command
    """

    _ModelBase__schema = {
        # Hash of configuration file uploaded to ReqMgr2
        'config_id': '',
        # Hash of harvesting configuration file uploaded to ReqMgr2
        'harvesting_config_id': '',
        # What conditions to use. This has to be specified
        'conditions': '',
        # What data tier to use
        'datatier': [],
        # Specify the file where the code to modify the process object is stored
        # If inline_custom is set to 1, then inline the customisation file
        'customise': '',
        # Specify which era to use (e.g. "run2")
        'era': '',
        # What event content to write out
        'eventcontent': [],
        # Freeform attributes appended at the end
        'extra': '',
        # How many threads should CMSSW use
        'nThreads': 1,
        # Scenario overriding standard settings: 'pp', 'cosmics', 'nocoll', 'HeavyIons'
        'scenario': 'pp',
        # The desired step. The possible values are:
        # GEN,SIM,DIGI,L1,DIGI2RAW,HLT,RAW2DIGI,RECO,POSTRECO,
        # DQM,ALCA,VALIDATION,HARVESTING, NONE or ALL
        'step': []}

    _lambda_checks = {
        'conditions': lambda c: ModelBase.matches_regex(c, '[a-zA-Z0-9_]{0,50}'),
        'era': lambda e: ModelBase.matches_regex(e, '[a-zA-Z0-9_\\,]{0,50}'),
        'nThreads': lambda n: 0 < n < 64,
        'scenario': lambda s: s in ('pp', 'cosmics', 'nocoll', 'HeavyIons'),
        '__datatier': lambda s: s in ('AOD', 'MINIAOD', 'NANOAOD', 'DQMIO', 'USER', 'ALCARECO'),
        '__eventcontent': lambda s: s in ('AOD', 'MINIAOD', 'NANOAOD', 'DQM', 'NANOEDMAOD'),
        '__step': lambda s: (s in ('RAW2DIGI', 'L1Reco', 'RECO', 'EI', 'PAT', 'DQM', 'NANO') or
                             s.startswith('ALCA') or s.startswith('DQM') or s.startswith('SKIM'))
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def get_prepid(self):
        return 'Sequence'

    def needs_harvesting(self):
        """
        Return if this sequence produces input file for harvesting
        and harvesting step is needed
        """
        for step in self.get('step'):
            if step == 'DQM' or step.startswith('DQM:'):
                return True

        return False
