"""
Module that contains ModelBase class
"""
from core_lib.model.model_base import ModelBase as PdmVModelBase
from core_lib.utils.common_utils import make_regex_matcher as regex


class ModelBase(PdmVModelBase):
    """
    Base class for all ReReco objects in the system
    Has some convenience methods as well as somewhat smart setter
    Contains a bunch of sanity checks
    """

    cmssw_check = regex('CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}')
    dataset_check = regex('^/[a-zA-Z0-9\\-_]{1,99}/[a-zA-Z0-9\\.\\-_]{1,199}/[A-Z\\-]{1,50}$')
    processing_string_check = regex('[a-zA-Z0-9_]{1,100}')
    request_id_check = regex('[a-zA-Z0-9\\-_]{1,100}')
    runs_json_path_check = regex('[a-zA-Z0-9/\\-_]{0,150}(\\.json|\\.txt)?')
    subcampaign_id_check = regex('[a-zA-Z0-9]{1,25}\\-[a-zA-Z0-9_]{1,35}')
    ticket_id_check = regex('[a-zA-Z0-9_\\-]{1,75}')

    default_lambda_checks = {
        'cmssw_release': cmssw_check,
        'dataset': dataset_check,
        'energy': lambda energy: 0 <= energy <= 100,
        'memory': lambda mem: 0 <= mem <= 64000,
        'processing_string': processing_string_check,
        'priority': lambda priority: 20000 <= priority <= 1000000,
        'subcampaign': subcampaign_id_check,
    }
