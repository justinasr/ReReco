from core.controller.controller_base import ControllerBase
from core.model.campaign_ticket import CampaignTicket
from core.utils.cmsweb import ConnectionWrapper
from core.database.database import Database
import json
import time


class CampaignTicketController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'campaign_tickets'
        self.model_class = CampaignTicket

    def check_for_create(self, obj):
        """
        Perform checks on object before adding it to database
        """
        campaign_database = Database('campaigns')
        campaign_name = obj.get('campaign_name')
        if not campaign_database.document_exists(campaign_name):
            raise Exception('Campaign %s does not exist' % (campaign_name))

        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        """
        Compare existing and updated objects to see if update is valid
        """
        if 'campaign_name' in changed_values:
            campaign_database = Database('campaigns')
            campaign_name = new_obj.get('campaign_name')
            if not campaign_database.document_exists(campaign_name):
                raise Exception('Campaign %s does not exist' % (campaign_name))

        return True

    def check_for_delete(self, obj):
        """
        Perform checks on object before deleting it from database
        """
        return True

    def get_datasets(self, query):
        if not query:
            return []

        start_time = time.time()
        connection_wrapper = ConnectionWrapper()
        response = connection_wrapper.api('POST', '/dbs/prod/global/DBSReader/datasetlist', {'dataset': query})
        response = json.loads(response.decode('utf-8'))
        datasets = [x['dataset'] for x in response]
        end_time = time.time()
        self.logger.debug('Sleeping for %.2fs', max(end_time - start_time, 10) * 0.1)
        time.sleep(max(end_time - start_time, 10) * 0.1)
        self.logger.info('Got %s datasets from DBS for query %s in %.2fs', len(datasets), query, end_time - start_time)
        return datasets

    def get_editing_info(self, campaign_ticket):
        editing_info = {k: not k.startswith('_') for k in campaign_ticket.json().keys()}
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
        editing_info['campaign_name'] = not bool(campaign_ticket.get('created_requests'))
        editing_info['processing_string'] = editing_info['campaign_name']
        editing_info['input_datasets'] = editing_info['campaign_name']
        return editing_info
