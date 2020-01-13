from core.controller.controller_base import ControllerBase
from core.model.campaign_ticket import CampaignTicket
from core.utils.cmsweb import ConnectionWrapper
from core.database.database import Database
from core.controller.request_controller import RequestController
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
        is_new = campaign_ticket.get('status') == 'new'
        editing_info['campaign_name'] = is_new
        editing_info['processing_string'] = is_new
        editing_info['input_datasets'] = is_new
        return editing_info

    def create_requests_for_ticket(self, campaign_ticket):
        ticket_prepid = campaign_ticket.get_prepid()
        with self.locker.get_lock(ticket_prepid):
            request_controller = RequestController()
            campaign_name = campaign_ticket.get('campaign_name')
            created_requests = campaign_ticket.get('created_requests')
            for input_dataset in campaign_ticket.get('input_datasets'):
                created_request_json = request_controller.create({'member_of_campaign': campaign_name, 'input_dataset': input_dataset})
                created_requests.append(created_request_json.get('prepid'))

            campaign_ticket.set('created_requests', created_requests)
            campaign_ticket.set('status', 'done')
            self.update(campaign_ticket.json())

        return created_requests
