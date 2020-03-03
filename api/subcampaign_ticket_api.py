"""
Module that contains all subcampaign ticket APIs
"""
import json
import flask
from flask import request
from api.api_base import APIBase
from core.controller.subcampaign_ticket_controller import SubcampaignTicketController
from core.model.subcampaign_ticket import SubcampaignTicket


subcampaign_ticket_controller = SubcampaignTicketController()


class CreateSubcampaignTicketAPI(APIBase):
    """
    Endpoint for creating subcampaign ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a subcampaign ticket with the provided JSON content
        """
        data = flask.request.data
        subcampaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_ticket_controller.create(subcampaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteSubcampaignTicketAPI(APIBase):
    """
    Endpoint for deleting subcampaigns tickets
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a subcampaign with the provided JSON content
        """
        data = flask.request.data
        subcampaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_ticket_controller.delete(subcampaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateSubcampaignTicketAPI(APIBase):
    """
    Endpoint for updating subcampaign tickets
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Update a subcampaign with the provided JSON content
        """
        data = flask.request.data
        subcampaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_ticket_controller.update(subcampaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetSubcampaignTicketAPI(APIBase):
    """
    Endpoint for retrieving a single subcampaign ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single subcampaign with given prepid
        """
        obj = subcampaign_ticket_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetSubcampaignTicketDatasetsAPI(APIBase):
    """
    Endpoint for getting list of datasets from DBS for subcampaign ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get a single subcampaign with given prepid
        """
        query = request.args.get('q')
        if not query:
            raise Exception('No input was supplied')

        obj = subcampaign_ticket_controller.get_datasets(query)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetEditableSubcampaignTicketAPI(APIBase):
    """
    Endpoint for getting information on which subcampaign ticket fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single subcampaign with given prepid
        """
        if prepid:
            subcampaign_ticket = subcampaign_ticket_controller.get(prepid)
        else:
            subcampaign_ticket = SubcampaignTicket()

        editing_info = subcampaign_ticket_controller.get_editing_info(subcampaign_ticket)
        return self.output_text({'response': {'object': subcampaign_ticket.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})


class CreateRequestsForSubcampaignTicketAPI(APIBase):
    """
    Endpoing for creating requests from a subcampaign ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Create requests for give subcampaign ticket
        """
        data = flask.request.data
        request_data = json.loads(data.decode('utf-8'))
        prepid = request_data.get('prepid')
        if not prepid:
            self.logger.error('No prepid in given data: %s', json.dumps(request_data, indent=2))
            raise Exception('No prepid in submitted data')

        ticket = subcampaign_ticket_controller.get(prepid)
        if not ticket:
            raise Exception(f'Subcampaign ticket "{prepid}" does not exist')

        result = subcampaign_ticket_controller.create_requests_for_ticket(ticket)
        return self.output_text({'response': result, 'success': True, 'message': ''})


class GetSubcampaignTicketTwikiAPI(APIBase):
    """
    Endpoing for getting a twiki snippet for given subcampaign ticket
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get twiki snippet for subcampaign ticket
        """
        subcampaign_ticket = subcampaign_ticket_controller.get(prepid)
        twiki = subcampaign_ticket_controller.get_twiki_snippet(subcampaign_ticket)
        return self.output_text(twiki, content_type='text/plain')
