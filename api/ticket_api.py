"""
Module that contains all ticket APIs
"""
import json
import flask
from flask import request
from core_lib.api.api_base import APIBase
from core_lib.utils.common_utils import clean_split
from core.controller.ticket_controller import TicketController
from core.model.ticket import Ticket


ticket_controller = TicketController()


class CreateTicketAPI(APIBase):
    """
    Endpoint for creating ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def put(self):
        """
        Create a ticket with the provided JSON content
        """
        data = flask.request.data
        ticket_json = json.loads(data.decode('utf-8'))
        obj = ticket_controller.create(ticket_json)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class DeleteTicketAPI(APIBase):
    """
    Endpoint for deleting tickets
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def delete(self):
        """
        Delete a with the provided JSON content
        """
        data = flask.request.data
        ticket_json = json.loads(data.decode('utf-8'))
        obj = ticket_controller.delete(ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateTicketAPI(APIBase):
    """
    Endpoint for updating tickets
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Update a with the provided JSON content
        """
        data = flask.request.data
        ticket_json = json.loads(data.decode('utf-8'))
        obj = ticket_controller.update(ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetTicketAPI(APIBase):
    """
    Endpoint for retrieving a single ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single with given prepid
        """
        obj = ticket_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetTicketDatasetsAPI(APIBase):
    """
    Endpoint for getting list of datasets from DBS for ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def get(self):
        """
        Get a single with given prepid
        """
        query = request.args.get('q')
        if not query:
            raise Exception('No input was supplied')

        exclude = request.args.get('exclude', '')
        exclude = clean_split(exclude)
        obj = ticket_controller.get_datasets(query, exclude)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetEditableTicketAPI(APIBase):
    """
    Endpoint for getting information on which ticket fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single with given prepid
        """
        if prepid:
            ticket = ticket_controller.get(prepid)
        else:
            ticket = Ticket()

        editing_info = ticket_controller.get_editing_info(ticket)
        return self.output_text({'response': {'object': ticket.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})


class CreateRequestsForTicketAPI(APIBase):
    """
    Endpoing for creating requests from a ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Create requests for given ticket
        """
        data = flask.request.data
        request_data = json.loads(data.decode('utf-8'))
        prepid = request_data.get('prepid')
        if not prepid:
            self.logger.error('No prepid in given data: %s', json.dumps(request_data, indent=2))
            raise Exception('No prepid in submitted data')

        ticket = ticket_controller.get(prepid)
        if not ticket:
            raise Exception(f'Ticket "{prepid}" does not exist')

        result = ticket_controller.create_requests_for_ticket(ticket)
        return self.output_text({'response': result, 'success': True, 'message': ''})


class GetTicketTwikiAPI(APIBase):
    """
    Endpoing for getting a twiki snippet for given ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get twiki snippet for ticket
        """
        ticket = ticket_controller.get(prepid)
        twiki = ticket_controller.get_twiki_snippet(ticket)
        return self.output_text(twiki, content_type='text/plain')
