"""
Module that contains SubcampaignController class
"""
import xml.etree.ElementTree as XMLet
from core_lib.database.database import Database
from core_lib.controller.controller_base import ControllerBase
from core_lib.utils.connection_wrapper import ConnectionWrapper
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

    def get_scram_arch(self, cmssw_release):
        """
        Get scram arch from
        https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1
        """
        if not cmssw_release:
            return None

        self.logger.debug('Downloading releases XML')
        conn = ConnectionWrapper(host='cmssdt.cern.ch')
        response = conn.api('GET', '/SDT/cgi-bin/ReleasesXML?anytype=1')
        self.logger.debug('Downloaded releases XML')
        root = XMLet.fromstring(response)
        for architecture in root:
            if architecture.tag != 'architecture':
                # This should never happen as children should be <architecture>
                continue

            scram_arch = architecture.attrib.get('name')
            for release in architecture:
                if release.attrib.get('label') == cmssw_release:
                    self.logger.debug('Scram arch for %s is %s', cmssw_release, scram_arch)
                    return scram_arch

        self.logger.warning('Could not find scram arch for %s', cmssw_release)
        return None
