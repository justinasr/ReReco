"""
Module that contains SubcampaignController class
"""
from core_lib.database.database import Database
from core_lib.controller.controller_base import ControllerBase
from core_lib.utils.common_utils import get_scram_arch
from core.model.subcampaign import Subcampaign
from core.model.sequence import Sequence


class SubcampaignController(ControllerBase):
    """
    Controller that has all actions related to a subcampaign
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'subcampaigns'
        self.model_class = Subcampaign

    def check_for_delete(self, obj):
        prepid = obj.get('prepid')
        requests_db = Database('requests')
        requests = requests_db.query(f'subcampaign={prepid}')
        if requests:
            raise Exception(f'It is not allowed to delete subcampaigns that have existing '
                            f'requests. {prepid} has {len(requests)} requests')

        return True

    def before_create(self, obj):
        cmssw_release = obj.get('cmssw_release')
        scram_arch = get_scram_arch(cmssw_release)
        if not scram_arch:
            raise Exception(f'Could not find scram_arch for {cmssw_release}')

        obj.set('scram_arch', scram_arch)

    def before_update(self, old_obj, new_obj, changed_values):
        if old_obj.get('cmssw_release') != new_obj.get('cmssw_release'):
            cmssw_release = new_obj.get('cmssw_release')
            scram_arch = get_scram_arch(cmssw_release)
            if not scram_arch:
                raise Exception(f'Could not find scram_arch for {cmssw_release}')

            new_obj.set('scram_arch', scram_arch)

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        creating_new = not bool(prepid)
        editing_info['prepid'] = creating_new
        editing_info['notes'] = True
        editing_info['energy'] = True
        editing_info['sequences'] = True
        editing_info['memory'] = True
        editing_info['runs_json_path'] = True
        editing_info['cmssw_release'] = True

        return editing_info

    def get_default_sequence(self, subcampaign):
        """
        Return a default sequence for a subcampaign
        """
        self.logger.debug('Creating a default sequence for %s', subcampaign.get_prepid())
        sequence = Sequence.schema()
        return sequence
