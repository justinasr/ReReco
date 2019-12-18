"""
Module that contains all campaign ticket APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.campaign_ticket_controller import CampaignTicketController
from core.model.campaign_ticket import CampaignTicket
from flask import request


campaign_ticket_controller = CampaignTicketController()


class CreateCampaignTicketAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a campaign ticket with the provided JSON content
        """
        data = flask.request.data
        campaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = campaign_ticket_controller.create(campaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteCampaignTicketAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a campaign with the provided JSON content
        """
        data = flask.request.data
        campaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = campaign_ticket_controller.delete(campaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateCampaignTicketAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Update a campaign with the provided JSON content
        """
        data = flask.request.data
        campaign_ticket_json = json.loads(data.decode('utf-8'))
        obj = campaign_ticket_controller.update(campaign_ticket_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetCampaignTicketAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single campaign with given prepid
        """
        obj = campaign_ticket_controller.get(prepid)
        return self.output_text({'response': obj.json(), 'success': True, 'message': ''})


class GetCampaignTicketDatasetsAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get a single campaign with given prepid
        """
        query = request.args.get('q')
        if not query:
            raise Exception('No input was supplied')

        obj = campaign_ticket_controller.get_datasets(query)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetEditableCampaignTicketAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single campaign with given prepid
        """
        if prepid:
            campaign_ticket = campaign_ticket_controller.get(prepid)
        else:
            campaign_ticket = CampaignTicket()

        editing_info = campaign_ticket_controller.get_editing_info(campaign_ticket)
        return self.output_text({'response': {'object': campaign_ticket.json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})
