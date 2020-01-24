"""
Module that contains all request APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.request_controller import RequestController
from core.model.request import Request


request_controller = RequestController()


class CreateRequestAPI(APIBase):
    """
    Endpoint for creating a request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a request with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        obj = request_controller.create(request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class DeleteRequestAPI(APIBase):
    """
    Endpoint for deleting a request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a request with the provided JSON content
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        obj = request_controller.delete(request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class UpdateRequestAPI(APIBase):
    """
    Endpoint for updating a request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Update a request with the provided JSON content
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        obj = request_controller.update(request_json)
        return self.output_text({'response': obj, 'success': True, 'message': ''})


class GetRequestAPI(APIBase):
    """
    Endpoint for retrieving a single request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single request with given prepid
        """
        obj = request_controller.get(prepid)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class GetEditableRequestAPI(APIBase):
    """
    Endpoint for getting information on which request fields are editable
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a single request with given prepid
        """
        if prepid:
            request = request_controller.get(prepid)
        else:
            request = Request()

        editing_info = request_controller.get_editing_info(request)
        return self.output_text({'response': {'object': request.get_json(),
                                              'editing_info': editing_info},
                                 'success': True,
                                 'message': ''})


class GetCMSDriverCommands(APIBase):
    """
    Endpoint for getting a bash script with cmsDriver.py commands of request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a text file with request's cmsDriver.py commands
        """
        request = request_controller.get(prepid)
        commands = request_controller.get_cmsdriver(request)
        return self.output_text(commands, content_type='text/plain')