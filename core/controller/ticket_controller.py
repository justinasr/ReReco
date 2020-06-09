"""
Module that contains TicketController class
"""
import json
import time
from core.model.ticket import Ticket
from core.utils.connection_wrapper import ConnectionWrapper
from core.utils.settings import Settings
from core.database.database import Database
from core.controller.controller_base import ControllerBase
from core.controller.request_controller import RequestController


class TicketController(ControllerBase):
    """
    Controller that has all actions related to a ticket
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'tickets'
        self.model_class = Ticket

    def create(self, json_data):
        # Clean up the input
        ticket_db = Database(self.database_name)
        json_data['prepid'] = 'Temp00001'
        ticket = Ticket(json_input=json_data)
        # Use first subcampaign name for prepid
        subcampaign_name = ticket.get('steps')[0]['subcampaign']
        processing_string = ticket.get('steps')[0]['processing_string']
        prepid_middle_part = f'{subcampaign_name}-{processing_string}'
        with self.locker.get_lock(f'generate-ticket-prepid-{prepid_middle_part}'):
            # Get a new serial number
            serial_numbers = ticket_db.query(f'prepid={prepid_middle_part}-*',
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
        subcampaign_names = [x['subcampaign'] for x in obj.get('steps')]
        for subcampaign_name in subcampaign_names:
            if not subcampaign_database.document_exists(subcampaign_name):
                raise Exception('Subcampaign %s does not exist' % (subcampaign_name))

        dataset_blacklist = set(Settings().get('dataset_blacklist'))
        for input_dataset in obj.get('input_datasets'):
            dataset = input_dataset.split('/')[1]
            if dataset in dataset_blacklist:
                raise Exception(f'Input dataset {input_dataset} is not '
                                f'allowed because {dataset} is in blacklist')

        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        if 'steps' in changed_values:
            subcampaign_database = Database('subcampaigns')
            subcampaign_names = [x['subcampaign'] for x in new_obj.get('steps')]
            for subcampaign_name in subcampaign_names:
                if not subcampaign_database.document_exists(subcampaign_name):
                    raise Exception('Subcampaign %s does not exist' % (subcampaign_name))

        if 'input_datasets' in changed_values:
            dataset_blacklist = set(Settings().get('dataset_blacklist'))
            for input_dataset in new_obj.get('input_datasets'):
                dataset = input_dataset.split('/')[1]
                if dataset in dataset_blacklist:
                    raise Exception(f'Input dataset {input_dataset} is not '
                                    f'allowed because {dataset} is in blacklist')

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

        with self.locker.get_lock('get-ticket-datasets'):
            start_time = time.time()
            connection_wrapper = ConnectionWrapper(host='cmsweb.cern.ch', max_attempts=1)
            response = connection_wrapper.api('POST',
                                              '/dbs/prod/global/DBSReader/datasetlist',
                                              {'dataset': query, 'detail': 1})

        response = json.loads(response.decode('utf-8'))
        valid_types = ('VALID', 'PRODUCTION')
        datasets = [x['dataset'] for x in response if x['dataset_access_type'] in valid_types]
        dataset_blacklist = set(Settings().get('dataset_blacklist'))
        datasets = [x for x in datasets if x.split('/')[1] not in dataset_blacklist]
        end_time = time.time()
        self.logger.info('Got %s datasets from DBS for query %s in %.2fs',
                         len(datasets),
                         query,
                         end_time - start_time)
        return datasets

    def get_editing_info(self, obj):
        editing_info = super().get_editing_info(obj)
        prepid = obj.get_prepid()
        status = obj.get('status')
        editing_info['prepid'] = False
        editing_info['history'] = False
        editing_info['steps'] = True
        editing_info['created_requests'] = False
        if status == 'done':
            editing_info['steps'] = False
            editing_info['priority'] = False

        return editing_info

    def create_requests_for_ticket(self, ticket):
        """
        Create requests from given ticket. Return list of request prepids
        """
        database = Database(self.database_name)
        ticket_prepid = ticket.get_prepid()
        created_requests = []
        dataset_blacklist = set(Settings().get('dataset_blacklist'))
        request_controller = RequestController()
        with self.locker.get_lock(ticket_prepid):
            ticket = Ticket(json_input=database.get(ticket_prepid))
            created_requests = ticket.get('created_requests')
            status = ticket.get('status')
            if status != 'new':
                raise Exception(f'Ticket is not new, it already has '
                                f'{len(created_requests)} requests created')

            # In case black list was updated after ticket was created
            for input_dataset in ticket.get('input_datasets'):
                dataset = input_dataset.split('/')[1]
                if dataset in dataset_blacklist:
                    raise Exception(f'Input dataset {input_dataset} is not '
                                    f'allowed because {dataset} is in blacklist')

            try:
                for input_dataset in ticket.get('input_datasets'):
                    last_request_prepid = None
                    for step_index, step in enumerate(ticket.get('steps')):
                        subcampaign_name = step['subcampaign']
                        processing_string = step['processing_string']
                        time_per_event = step['time_per_event']
                        size_per_event = step['size_per_event']
                        priority = step['priority']
                        submission_strategy = step['submission_strategy']
                        new_request_json = {'subcampaign': subcampaign_name,
                                            'priority': priority,
                                            'processing_string': processing_string,
                                            'time_per_event': time_per_event,
                                            'size_per_event': size_per_event,
                                            'input': {'dataset': '',
                                                      'request': '',
                                                      'submission_strategy': submission_strategy}}

                        if step_index == 0:
                            new_request_json['input']['dataset'] = input_dataset
                        else:
                            new_request_json['input']['request'] = last_request_prepid

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

                        request = request_controller.create(new_request_json)
                        created_requests.append(request)
                        last_request_prepid = request.get('prepid')

                        self.logger.info('Created %s', last_request_prepid)

                created_request_prepids = [r.get('prepid') for r in created_requests]
                ticket.set('created_requests', created_request_prepids)
                ticket.set('status', 'done')
                ticket.add_history('create_requests', created_request_prepids, None)
                database.save(ticket.get_json())
            except Exception as ex:
                # Delete created requests if there was an Exception
                for created_request in reversed(created_requests):
                    request_controller.delete({'prepid': created_request.get('prepid')})

                # And reraise the exception
                raise ex

        return [r.get('prepid') for r in created_requests]

    def get_twiki_snippet(self, ticket):
        """
        Generate tables for TWiki
        Requests are grouped by acquisition eras in input datasets
        """
        prepid = ticket.get_prepid()
        self.logger.debug('Returning TWiki snippet for %s', prepid)
        acquisition_eras = {}
        request_controller = RequestController()
        for request_prepid in ticket.get('created_requests'):
            request = request_controller.get(request_prepid)
            input_dataset = request.get('input_dataset')
            input_dataset_parts = [x.strip() for x in input_dataset.split('/') if x.strip()]
            acquisition_era = input_dataset_parts[1].split('-')[0]
            if acquisition_era not in acquisition_eras:
                acquisition_eras[acquisition_era] = []

            acquisition_eras[acquisition_era].append(request)

        output_strings = []
        pmp_url = 'https://cms-pdmv.cern.ch/pmp/historical?r='
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
                output_strings.append(f'| {dataset} | [[{pmp_url}{prepid}][{prepid}]] | {runs} |')

            output_strings.append('\n')

        return '\n'.join(output_strings).strip()
