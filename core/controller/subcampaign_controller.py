"""
Module that contains SubcampaignController class
"""
import xml.etree.ElementTree as XMLet
from core_lib.database.database import Database
from core_lib.controller.controller_base import ControllerBase
from core_lib.utils.connection_wrapper import ConnectionWrapper
from core_lib.utils.locker import Locker
from core_lib.utils.cache import TimeoutCache
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
        if not hasattr(self.__class__, 'scram_arch_cache'):
            self.__class__.scram_arch_cache = TimeoutCache(3600)

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
        scram_arch = self.get_scram_arch(cmssw_release)
        obj.set('scram_arch', scram_arch)

    def before_update(self, obj):
        cmssw_release = obj.get('cmssw_release')
        scram_arch = self.get_scram_arch(cmssw_release)
        obj.set('scram_arch', scram_arch)

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
        if not creating_new:
            requests_db = Database('requests')
            subcampaign_requests = requests_db.query(f'subcampaign={prepid}')
            editing_info['cmssw_release'] = not bool(subcampaign_requests)
        else:
            editing_info['cmssw_release'] = True

        return editing_info

    def get_default_sequence(self, subcampaign):
        """
        Return a default sequence for a subcampaign
        """
        self.logger.debug('Creating a default sequence for %s', subcampaign.get_prepid())
        sequence = Sequence.schema()
        return sequence

    @classmethod
    def get_scram_arch(cls, cmssw_release, refetch_if_needed=True):
        """
        Get scram arch from
        https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1
        Cache it in SubcampaignController class
        """
        if not cmssw_release:
            return None

        cache = cls.scram_arch_cache
        releases = cls.scram_arch_cache.get('releases', {})
        cached_value = releases.get(cmssw_release)
        if cached_value:
            return cached_value

        if not refetch_if_needed:
            return None

        with Locker().get_lock('relval-controller-get-scram-arch'):
            # Maybe cache got updated while waiting for a lock
            cached_value = cls.get_scram_arch(cmssw_release, False)
            if cached_value:
                return cached_value

            connection = ConnectionWrapper(host='cmssdt.cern.ch')
            response = connection.api('GET', '/SDT/cgi-bin/ReleasesXML?anytype=1')
            root = XMLet.fromstring(response)
            releases = {}
            for architecture in root:
                if architecture.tag != 'architecture':
                    # This should never happen as children should be <architecture>
                    continue

                scram_arch = architecture.attrib.get('name')
                for release in architecture:
                    releases[release.attrib.get('label')] = scram_arch

            cache.set('releases', releases)

        return cls.get_scram_arch(cmssw_release, False)
