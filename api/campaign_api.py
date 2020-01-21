"""
Module that contains all campaign APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.campaign_controller import CampaignController
from core.model.campaign import Campaign


campaign_controller = CampaignController()


class CreateCampaignAPI(APIBase):
    """
    Enpoint for creating campaigns
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a campaign with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        campaign_json = json.loads(data.decode('utf-8'))
        obj = campaign_controller.create(campaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteCampaignAPI(APIBase):
    """
    Endpoint for deleting campaigns
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a campaign with the provided JSON content
        """
        data = flask.request.data
        campaign_json = json.loads(data.decode('utf-8'))
        obj = campaign_controller.delete(campaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateCampaignAPI(APIBase):
    """
    Endpoint for updating campaigns
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Update a campaign with the provided JSON content
        """
        data = flask.request.data
        campaign_json = json.loads(data.decode('utf-8'))
        obj = campaign_controller.update(campaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetCampaignAPI(APIBase):
    """
    Endpoint for retrieving a single campaign
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single campaign with given prepid
        """
        obj = campaign_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetEditableCampaignAPI(APIBase):
    """
    Endpoint for getting information on which campaign fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single campaign with given prepid
        """
        if prepid:
            campaign = campaign_controller.get(prepid)
        else:
            campaign = Campaign()

        editing_info = campaign_controller.get_editing_info(campaign)
        return self.output_text({'response': {'object': campaign.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})


class GetDefaultCampaignSequenceAPI(APIBase):
    """
    Endpoint for getting a default (empty) sequence that could be used as a template
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a default sequence that could be used as a template
        """
        if prepid:
            campaign = campaign_controller.get(prepid)
        else:
            campaign = Campaign()

        sequence = campaign_controller.get_default_sequence(campaign)
        return self.output_text({'response': sequence.get_json(),
                                 'success': True,
                                 'message': ''})
