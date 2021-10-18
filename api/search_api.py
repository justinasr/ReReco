"""
Module that contains all search APIs
"""
import re
import time
import flask
from core_lib.api.api_base import APIBase
from core_lib.database.database import Database
from core.model.subcampaign import Subcampaign
from core.model.ticket import Ticket
from core.model.request import Request


class SearchAPI(APIBase):
    """
    Endpoint that is used for search in the database
    """

    def __init__(self):
        APIBase.__init__(self)
        self.classes = {'subcampaigns': Subcampaign,
                        'requests': Request,
                        'tickets': Ticket}

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Perform a search
        """
        args = flask.request.args.to_dict()
        if args is None:
            args = {}

        db_name = args.pop('db_name', None)
        page = int(args.pop('page', 0))
        limit = int(args.pop('limit', 20))
        sort = args.pop('sort', None)
        sort_asc = args.pop('sort_asc', 'true').lower() == 'true'

        # Special cases
        from_ticket = args.pop('ticket', None)
        if db_name == 'requests' and from_ticket:
            ticket_database = Database('tickets')
            ticket = ticket_database.get(from_ticket)
            created_requests = ','.join(ticket['created_requests'])
            prepid_query = args.pop('prepid', '')
            args['prepid'] = ('%s,%s' % (prepid_query, created_requests)).strip(',')

        limit = max(1, min(limit, 500))
        query_string = '&&'.join(['%s=%s' % (pair) for pair in args.items()])
        database = Database(db_name)
        query_string = database.build_query_with_types(query_string, self.classes[db_name])
        results, total_rows = database.query_with_total_rows(query_string=query_string,
                                                             page=page,
                                                             limit=limit,
                                                             sort_attr=sort,
                                                             sort_asc=sort_asc,
                                                             ignore_case=True)


        return self.output_text({'response': {'results': results,
                                              'total_rows': total_rows},
                                 'success': True,
                                 'message': ''})


class SuggestionsAPI(APIBase):
    """
    Endpoint that is used to fetch suggestions
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Return a list of prepid suggestions for given query
        """
        args = flask.request.args.to_dict()
        if args is None:
            args = {}

        db_name = args.pop('db_name', None)
        query = args.pop('query', None).replace(' ', '.*')
        limit = max(1, min(50, args.pop('limit', 20)))

        if not db_name or not query:
            raise Exception('Bad db_name or query parameter')

        database = Database(db_name)
        db_query = {'prepid': re.compile(f'.*{query}.*', re.IGNORECASE)}
        results = database.collection.find(db_query).limit(limit)
        results = [x['prepid'] for x in results]

        return self.output_text({'response': results,
                                 'success': True,
                                 'message': ''})


class WildSearchAPI(APIBase):
    """
    Endpoint that is used for abstract search in the whole database
    """

    def __init__(self):
        APIBase.__init__(self)
        self.classes = {'subcampaigns': Subcampaign,
                        'requests': Request,
                        'tickets': Ticket}

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Perform a search
        """
        args = flask.request.args.to_dict()
        if args is None:
            args = {}

        query = args.pop('q', None)
        if not query:
            return self.output_text({'response': [],
                                     'success': True,
                                     'message': 'Query string too short'})

        query = query.strip().replace(' ', '*')
        if len(query) < 3:
            return self.output_text({'response': [],
                                     'success': True,
                                     'message': 'Query string too short'})

        subcampaigns_db = Database('subcampaigns')
        tickets_db = Database('tickets')
        requests_db = Database('requests')

        attempts = [('requests', requests_db, 'prepid', False),
                    ('tickets', tickets_db, 'prepid', False),
                    ('subcampaigns', subcampaigns_db, 'prepid', False),
                    ('requests', requests_db, 'prepid', True),
                    ('tickets', tickets_db, 'prepid', True),
                    ('subcampaigns', subcampaigns_db, 'prepid', True),
                    # Tickets
                    ('tickets', tickets_db, 'subcampaign', True),
                    ('tickets', tickets_db, 'processing_string', True),
                    ('tickets', tickets_db, 'input', True),
                    # Requests
                    ('requests', requests_db, 'subcampaign', True),
                    ('requests', requests_db, 'processing_string', True),
                    ('requests', requests_db, 'input_dataset', True),
                    ('requests', requests_db, 'output_dataset', True),
                    ('requests', requests_db, 'workflow', True),]

        results = []
        used_values = set()
        for attempt in attempts:
            db_name = attempt[0]
            database = attempt[1]
            attr = attempt[2]
            wrap_in_wildcards = attempt[3]
            if wrap_in_wildcards:
                wrapped_query = f'*{query}*'
            else:
                wrapped_query = f'{query}'

            self.logger.info('Trying to query %s in %s', wrapped_query, db_name)
            typed_query = database.build_query_with_types(f'{attr}={wrapped_query}',
                                                          self.classes[db_name])
            query_results = database.query(typed_query, 0, 5, ignore_case=True)
            for result in query_results:
                values = self.extract_values(result, attr, wrapped_query, db_name)
                for value in values:
                    key = f'{db_name}:{attr}:{value}'
                    if key not in used_values:
                        used_values.add(key)
                        results.append({'value': value,
                                        'attribute': attr,
                                        'database': db_name})

            # Limit results to 20 to save DB some queries
            if len(results) >= 20:
                results = results[:20]
                break

            # Limit DB query rate as this is very expensive
            time.sleep(0.075)

        return self.output_text({'response': results,
                                 'success': True,
                                 'message': ''})

    def extract_values(self, item, attribute, query, db_name):
        """
        Return a list of one or multiple values got from an object
        One object might have multiple values, e.g. output datasets
        """
        if attribute in item and attribute != 'input':
            return [item[attribute]]

        values = []
        matcher = re.compile(query.replace('*', '.*'), re.IGNORECASE)
        self.logger.info('Item: %s, attribute: %s, query: %s, db name: %s',
                         item['prepid'],
                         attribute,
                         query,
                         db_name)
        if db_name == 'tickets':
            if attribute in ('subcampaign', 'processing_string'):
                for step in item['steps']:
                    if matcher.fullmatch(step[attribute]):
                        values.append(step[attribute])
            elif attribute == 'input':
                for input_item in item['input']:
                    if matcher.fullmatch(input_item):
                        values.append(input_item)

        elif db_name == 'requests':
            if attribute == 'input_dataset':
                values.append(item['input']['dataset'])

            elif attribute == 'input_request':
                values.append(item['input']['request'])

            elif attribute == 'output_dataset':
                for dataset in item['output_datasets']:
                    if matcher.fullmatch(dataset):
                        values.append(dataset)

            elif attribute == 'workflow':
                for workflow in item['workflows']:
                    if matcher.fullmatch(workflow['name']):
                        values.append(workflow['name'])

        return values
