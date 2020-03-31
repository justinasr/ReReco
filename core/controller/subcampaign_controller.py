"""
Module that contains SubcampaignController class
"""
import xml.etree.ElementTree as XMLet
from core.controller.controller_base import ControllerBase
from core.model.subcampaign import Subcampaign
from core.model.sequence import Sequence
from core.database.database import Database
from core.utils.connection_wrapper import ConnectionWrapper


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
        new = not bool(prepid)
        editing_info['prepid'] = new
        editing_info['history'] = False
        editing_info['scram_arch'] = False
        if prepid:
            requests_db = Database('requests')
            subcampaign_requests = requests_db.query(f'subcampaign={prepid}')
            if subcampaign_requests:
                editing_info['step'] = False
                editing_info['cmssw_release'] = False

        return editing_info

    def get_default_sequence(self, subcampaign):
        """
        Return a default sequence for a subcampaign
        """
        self.logger.debug('Creating a default sequence for %s', subcampaign.get_prepid())
        sequence = Sequence()
        return sequence

    def __get_scram_arch(self, cmssw_release, xml):
        """
        Internal method for getting scram arch for given release out of given XML string
        """
        self.logger.debug('Getting scram arch for %s', cmssw_release)
        root = XMLet.fromstring(xml)
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

    def get_scram_arch(self, cmssw_release):
        """
        Get scram arch from
        https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1
        """

        self.logger.debug('Downloading releases XML')
        conn = ConnectionWrapper(host='cmssdt.cern.ch')
        response = conn.api('GET', f'/SDT/cgi-bin/ReleasesXML?anytype=1')
        scram_arch = self.__get_scram_arch(cmssw_release, response)
        if not scram_arch:
            raise Exception(f'Could not find SCRAM arch for {cmssw_release}')

        return scram_arch
