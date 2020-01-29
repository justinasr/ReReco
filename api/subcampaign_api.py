"""
Module that contains all subcampaign APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.subcampaign_controller import SubcampaignController
from core.model.subcampaign import Subcampaign


subcampaign_controller = SubcampaignController()


class CreateSubcampaignAPI(APIBase):
    """
    Enpoint for creating subcampaigns
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a subcampaign with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        subcampaign_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_controller.create(subcampaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteSubcampaignAPI(APIBase):
    """
    Endpoint for deleting subcampaigns
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
        subcampaign_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_controller.delete(subcampaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateSubcampaignAPI(APIBase):
    """
    Endpoint for updating subcampaigns
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
        subcampaign_json = json.loads(data.decode('utf-8'))
        obj = subcampaign_controller.update(subcampaign_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetSubcampaignAPI(APIBase):
    """
    Endpoint for retrieving a single subcampaign
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single subcampaign with given prepid
        """
        obj = subcampaign_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetEditableSubcampaignAPI(APIBase):
    """
    Endpoint for getting information on which subcampaign fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single subcampaign with given prepid
        """
        if prepid:
            subcampaign = subcampaign_controller.get(prepid)
        else:
            subcampaign = Subcampaign()

        editing_info = subcampaign_controller.get_editing_info(subcampaign)
        return self.output_text({'response': {'object': subcampaign.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})


class GetDefaultSubcampaignSequenceAPI(APIBase):
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
            subcampaign = subcampaign_controller.get(prepid)
        else:
            subcampaign = Subcampaign()

        sequence = subcampaign_controller.get_default_sequence(subcampaign)
        return self.output_text({'response': sequence.get_json(),
                                 'success': True,
                                 'message': ''})
