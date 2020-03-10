"""
Module that contains SubcampaignTicketController class
"""
import json
import time
from core.controller.controller_base import ControllerBase
from core.model.subcampaign_ticket import SubcampaignTicket
from core.utils.connection_wrapper import ConnectionWrapper
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

    def create(self, json_data):
        # Clean up the request input
        subcampaign_ticket_db = Database(self.database_name)
        json_data['prepid'] = 'SubcampaignTemp00001'
        subcampaign_ticket = SubcampaignTicket(json_input=json_data)
        subcampaign_name = subcampaign_ticket.get('subcampaign')
        processing_string = subcampaign_ticket.get('processing_string')
        prepid_middle_part = f'{subcampaign_name}-{processing_string}'
        with self.locker.get_lock(f'generate-subcampaign-ticket-prepid-{prepid_middle_part}'):
            # Get a new serial number
            serial_numbers = subcampaign_ticket_db.query(f'prepid={prepid_middle_part}-*',
                                                         limit=1,
                                                         sort_asc=False)
            if not serial_numbers:
                serial_number = 0
            else:
                serial_number = serial_numbers[0]['prepid']
                serial_number = int(serial_number.split('-')[-1])

            serial_number += 1
            # Form a new temporary prepid
            prepid = f'{prepid_middle_part}-{serial_number:05d}'
            json_data['prepid'] = prepid
            return super().create(json_data)

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

        with self.locker.get_lock('get-subcampaign-datasets'):
            start_time = time.time()
            connection_wrapper = ConnectionWrapper(host='cmsweb.cern.ch')
            response = connection_wrapper.api('POST',
                                              '/dbs/prod/global/DBSReader/datasetlist',
                                              {'dataset': query})

        response = json.loads(response.decode('utf-8'))
        datasets = [x['dataset'] for x in response]
        end_time = time.time()
        self.logger.info('Got %s datasets from DBS for query %s in %.2fs',
                         len(datasets),
                         query,
                         end_time - start_time)
        return datasets

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        new = not bool(prepid)
        status = obj.get('status')
        editing_info['prepid'] = False
        editing_info['history'] = False
        editing_info['subcampaign'] = new
        editing_info['processing_string'] = new
        editing_info['created_requests'] = False
        if status == 'done':
            editing_info['input_datasets'] = False
            editing_info['size_per_event'] = False
            editing_info['time_per_event'] = False

        return editing_info

    def create_requests_for_ticket(self, subcampaign_ticket):
        """
        Create requests from given subcampaign ticket. Return list of request prepids
        """
        database = Database('subcampaign_tickets')
        ticket_prepid = subcampaign_ticket.get_prepid()
        newly_created_request_jsons = []
        request_controller = RequestController()
        with self.locker.get_lock(ticket_prepid):
            subcampaign_ticket = SubcampaignTicket(json_input=database.get(ticket_prepid))
            created_requests = subcampaign_ticket.get('created_requests')
            status = subcampaign_ticket.get('status')
            if status != 'new':
                raise Exception(f'Ticket is not new, it already has '
                                f'{len(created_requests)} requests created')

            subcampaign_name = subcampaign_ticket.get('subcampaign')
            processing_string = subcampaign_ticket.get('processing_string')
            time_per_event = subcampaign_ticket.get('time_per_event')
            size_per_event = subcampaign_ticket.get('size_per_event')
            try:
                for input_dataset in subcampaign_ticket.get('input_datasets'):
                    new_request_json = {'subcampaign': subcampaign_name,
                                        'input_dataset': input_dataset,
                                        'processing_string': processing_string,
                                        'time_per_event': time_per_event,
                                        'size_per_event': size_per_event}
                    try:
                        runs = request_controller.get_runs(subcampaign_name, input_dataset)
                        new_request_json['runs'] = runs
                    except Exception as ex:
                        self.logger.error('Error getting runs for %s %s %s request. '
                                          'Will leave empty. Error:\n%s',
                                          subcampaign_name,
                                          input_dataset,
                                          processing_string,
                                          ex)

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

    def get_twiki_snippet(self, subcampaign_ticket):
        """
        Generate tables for TWiki
        Requests are grouped by acquisition eras in input datasets
        """
        acquisition_eras = {}
        request_controller = RequestController()
        for request_prepid in subcampaign_ticket.get('created_requests'):
            request = request_controller.get(request_prepid)
            input_dataset = request.get('input_dataset')
            input_dataset_parts = [x.strip() for x in input_dataset.split('/') if x.strip()]
            acquisition_era = input_dataset_parts[1].split('-')[0]
            if acquisition_era not in acquisition_eras:
                acquisition_eras[acquisition_era] = []

            acquisition_eras[acquisition_era].append(request)

        output_strings = []
        for acquisition_era, requests in acquisition_eras.items():
            output_strings.append(f'---+++ !{acquisition_era}\n')
            output_strings.append('| *DataSet* | *prepID monitoring* | *run* |')
            for request in requests:
                prepid = request.get_prepid()
                runs = request.get('runs')
                runs = ', '.join(str(r) for r in runs)
                input_dataset = request.get('input_dataset')
                input_dataset_parts = [x.strip() for x in input_dataset.split('/') if x.strip()]
                dataset = input_dataset_parts[0]
                output_strings.append(f'| {dataset} | [[https://cms-pdmv.cern.ch/pmp/historical?r={prepid}][{prepid}]] | {runs} |')

            output_strings.append('\n')

        return '\n'.join(output_strings).strip()
