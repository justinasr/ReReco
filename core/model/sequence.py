from core.model.model_base import ModelBase


class Sequence(ModelBase):

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

    __lambda_checks = {
        'conditions': lambda c: ModelBase.matches_regex(c, '[a-zA-Z0-9_]{0,50}'),
        'era': lambda e: ModelBase.matches_regex(e, '[a-zA-Z0-9_]{0,50}'),
        'nThreads': lambda n: n > 0 and n < 64,
        '__datatier': lambda s: s in ('AOD', 'MINIAOD', 'DQM'),
        '__eventcontent': lambda s: s in ('AOD', 'MINIAOD', 'DQM'),
        '__step': lambda s: s in ('GEN', 'SIM', 'DIGI', 'L1', 'DIGI2RAW', 'HLT', 'RAW2DIGI', 'RECO', 'POSTRECO', 'DQM', 'ALCA', 'HARVESTING')
    }

    def __init__(self, json_input=None):
        ModelBase.__init__(self, json_input)

    def check_attribute(self, attribute_name, attribute_value):
        if attribute_name in self.__lambda_checks:
            return self.__lambda_checks.get(attribute_name)(attribute_value)

        if attribute_name in ('datatier', 'eventcontent', 'step'):
            for value in attribute_value:
                if not self.__lambda_checks.get(f'__{attribute_name}')(value):
                    raise Exception(f'Invalid {attribute_name}: {value} in Sequence')

        return True

    def get_prepid(self):
        return 'Sequence'

    def cast_value_to_correct_type(self, attribute_name, attribute_value):
        if attribute_name in ('datatier', 'eventcontent', 'step'):
            if isinstance(attribute_value, str):
                return [x.strip() for x in attribute_value.split(',') if x.strip()]
            else:
                raise Exception('Cannot convert {attribute_name} of Sequence to correct type')

        return super().cast_value_to_correct_type(attribute_name, attribute_value)

    def before_attribute_check(self, attribute_name, attribute_value):
        if attribute_name in ('datatier', 'eventcontent', 'step'):
            return [x.strip() for x in attribute_value if x.strip()]

        return attribute_value
