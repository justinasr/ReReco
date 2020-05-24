"""
Module that contains all chained request APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.chained_request_controller import ChainedRequestController
from core.model.chained_request import ChainedRequest


chained_request_controller = ChainedRequestController()


class CreateChainedRequestAPI(APIBase):
    """
    Enpoint for creating chained requests
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def put(self):
        """
        Create a chained request with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        chained_request_json = json.loads(data.decode('utf-8'))
        obj = chained_request_controller.create(chained_request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteChainedRequestAPI(APIBase):
    """
    Endpoint for deleting chained requests
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def delete(self):
        """
        Delete a chained request with the provided JSON content
        """
        data = flask.request.data
        chained_request_json = json.loads(data.decode('utf-8'))
        obj = chained_request_controller.delete(chained_request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateChainedRequestAPI(APIBase):
    """
    Endpoint for updating chained requests
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Update a chained request with the provided JSON content
        """
        data = flask.request.data
        chained_request_json = json.loads(data.decode('utf-8'))
        obj = chained_request_controller.update(chained_request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetChainedRequestAPI(APIBase):
    """
    Endpoint for retrieving a single chained request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single chained_request with given prepid
        """
        obj = chained_request_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetEditableChainedRequestAPI(APIBase):
    """
    Endpoint for getting information on which chained request fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single chained request with given prepid
        """
        if prepid:
            chained_request = chained_request_controller.get(prepid)
        else:
            chained_request = ChainedRequest()

        editing_info = chained_request_controller.get_editing_info(chained_request)
        return self.output_text({'response': {'object': chained_request.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})
