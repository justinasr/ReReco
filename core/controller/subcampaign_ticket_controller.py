"""
Module that contains SubcampaignTicketController class
"""
import json
import time
from core.controller.controller_base import ControllerBase
from core.model.subcampaign_ticket import SubcampaignTicket
from core.utils.cmsweb import ConnectionWrapper
from core.database.database import Database
from core.controller.request_controller import RequestController


class SubcampaignTicketController(ControllerBase):
    """
    Controller that has all actions related to a subcampaign ticket
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'subcampaign_tickets'
        self.model_class = SubcampaignTicket

    def check_for_create(self, obj):
        subcampaign_database = Database('subcampaigns')
        subcampaign_name = obj.get('subcampaign')
        if not subcampaign_database.document_exists(subcampaign_name):
            raise Exception('Subcampaign %s does not exist' % (subcampaign_name))

        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        if 'subcampaign' in changed_values:
            subcampaign_database = Database('subcampaigns')
            subcampaign_name = new_obj.get('subcampaign')
            if not subcampaign_database.document_exists(subcampaign_name):
                raise Exception('Subcampaign %s does not exist' % (subcampaign_name))

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
        newly_created = not bool(editing_info.get('prepid'))
        status = obj.get('status')
        editing_info['prepid'] = newly_created
        editing_info['history'] = False
        editing_info['created_requests'] = False
        if status == 'done':
            editing_info['subcampaign'] = False
            editing_info['processing_string'] = False
            editing_info['input_datasets'] = False

        return editing_info

    def create_requests_for_ticket(self, subcampaign_ticket):
        """
        Create requests from given subcampaign ticket. Return list of request prepids
        """
        database = Database('subcampaign_tickets')
        ticket_prepid = subcampaign_ticket.get_prepid()
        with self.locker.get_lock(ticket_prepid):
            subcampaign_ticket = SubcampaignTicket(json_input=database.get(ticket_prepid))
            created_requests = subcampaign_ticket.get('created_requests')
            newly_created_request_jsons = []
            status = subcampaign_ticket.get('status')
            if status != 'new':
                raise Exception(f'Ticket is not new, it already has '
                                f'{len(created_requests)} requests created')

            request_controller = RequestController()
            subcampaign_name = subcampaign_ticket.get('subcampaign')
            processing_string = subcampaign_ticket.get('processing_string')
            try:
                for input_dataset in subcampaign_ticket.get('input_datasets'):
                    new_request_json = {'subcampaign': subcampaign_name,
                                        'input_dataset': input_dataset,
                                        'processing_string': processing_string}
                    created_request_json = request_controller.create(new_request_json)
                    newly_created_request_jsons.append(created_request_json)

                created_requests.extend(r.get('prepid') for r in newly_created_request_jsons)
                subcampaign_ticket.set('created_requests', created_requests)
                subcampaign_ticket.set('status', 'done')
                subcampaign_ticket.add_history('create_requests', created_requests, None)
                database.save(subcampaign_ticket.get_json())
            except Exception as ex:
                # Delete created requests if there was an Exception
                for newly_created_request_json in newly_created_request_jsons:
                    request_controller.delete(newly_created_request_json)

                # And reraise the exception
                raise ex

        return created_requests
