"""
Module that contains ModelBase class
"""
import re
from core_lib.pdmv_model.model_base import ModelBase as PdmVModelBase


class ModelBase(PdmVModelBase):
    """
    Base class for all ReReco objects in the system
    Has some convenience methods as well as somewhat smart setter
    Contains a bunch of sanity checks
    """
    __cmssw_regex = 'CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}'  # CMSSW_ddd_ddd_ddd[_XXX...]
    __dataset_regex = '^/[a-zA-Z0-9\\-_]{1,99}/[a-zA-Z0-9\\.\\-_]{1,199}/[A-Z\\-]{1,50}$'
    __subcampaign_regex = '[a-zA-Z0-9]{1,25}\\-[a-zA-Z0-9_]{1,35}'
    default_lambda_checks = {
        'cmssw_release': lambda cmssw: ModelBase.matches_regex(cmssw, ModelBase.__cmssw_regex),
        'dataset': lambda ds: ModelBase.matches_regex(ds, ModelBase.__dataset_regex),
        'energy': lambda energy: 0 <= energy <= 100,
        'memory': lambda mem: 0 <= mem <= 64000,
        'processing_string': lambda ps: ModelBase.matches_regex(ps, '[a-zA-Z0-9_]{1,100}'),
        'priority': lambda priority: 20000 <= priority <= 1000000,
        'scram_arch': lambda sa: ModelBase.matches_regex(sa, '[a-z0-9_]{0,30}'),
        'subcampaign': lambda sc: ModelBase.matches_regex(sc, ModelBase.__subcampaign_regex),
    }
