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
        #
        'extra': '',
        # How many threads should CMSSW use
        'nThreads': 1,
        # The desired step. The possible values are:
        # GEN,SIM,DIGI,L1,DIGI2RAW,HLT,RAW2DIGI,RECO,POSTRECO,
        # DQM,ALCA,VALIDATION,HARVESTING, NONE or ALL
        'step': []}

    _lambda_checks = {
        'conditions': lambda c: ModelBase.matches_regex(c, '[a-zA-Z0-9_]{0,50}'),
        'era': lambda e: ModelBase.matches_regex(e, '[a-zA-Z0-9_]{0,50}'),
        'nThreads': lambda n: 0 < n < 64,
        '__datatier': lambda s: s in ('AOD', 'MINIAOD', 'DQMIO'),
        '__eventcontent': lambda s: s in ('AOD', 'MINIAOD', 'DQM'),
        '__step': lambda s: s in ('GEN', 'SIM', 'DIGI', 'L1', 'DIGI2RAW', 'HLT', 'RAW2DIGI', 'RECO', 'POSTRECO', 'DQM', 'ALCA', 'HARVESTING')
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def get_prepid(self):
        return 'Sequence'
