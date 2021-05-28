"""
Module that contains SubcampaignController class
"""
import json
from core_lib.database.database import Database
from core_lib.controller.controller_base import ControllerBase
from core_lib.utils.cache import TimeoutCache
from core_lib.utils.connection_wrapper import ConnectionWrapper
from core_lib.utils.global_config import Config
from core.model.subcampaign import Subcampaign
from core.model.sequence import Sequence


class SubcampaignController(ControllerBase):
    """
    Controller that has all actions related to a subcampaign
    """

    # DCS json cache
    __dcs_cache = TimeoutCache(7200)

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

    def get_dcs_json(self, subcampaign_name):
        """
        Fetch a dict of runs and lumisection ranges for a subcampaign
        """
        cached_value = self.__dcs_cache.get(subcampaign_name)
        if cached_value:
            return cached_value

        runs_json_path = self.get(subcampaign_name).get('runs_json_path')
        if not runs_json_path:
            return {}

        conn = ConnectionWrapper(host='cms-service-dqmdc.web.cern.ch',
                                 cert_file=Config.get('grid_user_cert'),
                                 key_file=Config.get('grid_user_key'))
        with self.locker.get_lock('get-dcs-runs'):
            response = conn.api('GET', f'/CAF/certification/{runs_json_path}')

        response = json.loads(response.decode('utf-8'))
        if not response:
            self.__dcs_cache.set(subcampaign_name, {})
            return {}

        self.__dcs_cache.set(subcampaign_name, response)
        return response
