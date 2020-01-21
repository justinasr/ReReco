"""
Module that contains CampaignTicketController class
"""
import json
import time
from core.controller.controller_base import ControllerBase
from core.model.campaign_ticket import CampaignTicket
from core.utils.cmsweb import ConnectionWrapper
from core.database.database import Database
from core.controller.request_controller import RequestController
from core.controller.campaign_controller import CampaignController


class CampaignTicketController(ControllerBase):
    """
    Controller that has all actions related to a campaign ticket
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'campaign_tickets'
        self.model_class = CampaignTicket

    def check_for_create(self, obj):
        campaign_database = Database('campaigns')
        campaign_name = obj.get('campaign')
        if not campaign_database.document_exists(campaign_name):
            raise Exception('Campaign %s does not exist' % (campaign_name))

        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        if 'campaign' in changed_values:
            campaign_database = Database('campaigns')
            campaign_name = new_obj.get('campaign')
            if not campaign_database.document_exists(campaign_name):
                raise Exception('Campaign %s does not exist' % (campaign_name))

        return True

    def check_for_delete(self, obj):
        created_requests = obj.get('created_requests')
        prepid = obj.get('prepid')
        if created_requests:
            raise Exception(f'It is not allowed to delete tickets that have requests created. '
                            f'{prepid} has {len(created_requests)} requests')

        return True

    def get_datasets(self, query):
        """
        Query DBS for list of datasets
        """
        if not query:
            return []

        start_time = time.time()
        connection_wrapper = ConnectionWrapper()
        response = connection_wrapper.api('POST',
                                          '/dbs/prod/global/DBSReader/datasetlist',
                                          {'dataset': query})
        response = json.loads(response.decode('utf-8'))
        datasets = [x['dataset'] for x in response]
        end_time = time.time()
        self.logger.debug('Sleeping for %.2fs', max(end_time - start_time, 10) * 0.1)
        time.sleep(max(end_time - start_time, 10) * 0.1)
        self.logger.info('Got %s datasets from DBS for query %s in %.2fs',
                         len(datasets),
                         query,
                         end_time - start_time)
        return datasets

    def get_editing_info(self, obj):
        editing_info = {k: not k.startswith('_') for k in obj.get_json().keys()}
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
        is_new = obj.get('status') == 'new'
        editing_info['campaign'] = is_new
        editing_info['processing_string'] = is_new
        editing_info['input_datasets'] = is_new
        editing_info['created_requests'] = False
        return editing_info

    def create_requests_for_ticket(self, campaign_ticket):
        """
        Create requests from given campaign ticket. Return list of request prepids
        """
        ticket_prepid = campaign_ticket.get_prepid()
        with self.locker.get_lock(ticket_prepid):
            created_requests = campaign_ticket.get('created_requests')
            status = campaign_ticket.get('status')
            if status != 'new':
                raise Exception(f'Ticket is not new, it already has '
                                f'{len(created_requests)} requests created')

            request_controller = RequestController()
            campaign_controller = CampaignController()
            campaign_name = campaign_ticket.get('campaign')
            campaign = campaign_controller.get(campaign_name)
            processing_string = campaign_ticket.get('processing_string')
            for input_dataset in campaign_ticket.get('input_datasets'):
                new_request_json = {'member_of_campaign': campaign_name,
                                    'input_dataset': input_dataset,
                                    'processing_string': processing_string,
                                    'type': campaign.get('type'),
                                    'step': campaign.get('step'),
                                    'memory': campaign.get('memory'),
                                    'cmssw_release': campaign.get('cmssw_release'),
                                    'energy': campaign.get('energy')}
                created_request_json = request_controller.create(new_request_json)
                created_requests.append(created_request_json.get('prepid'))

            campaign_ticket.set('created_requests', created_requests)
            campaign_ticket.set('status', 'done')
            campaign_ticket.add_history('create_requests', created_requests, None)
            database = Database('campaign_tickets')
            database.save(campaign_ticket.get_json())

        return created_requests
