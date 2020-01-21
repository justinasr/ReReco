"""
Module that contains all flow APIs
"""
import json
import flask
from api.api_base import APIBase
from core.controller.flow_controller import FlowController


flow_controller = FlowController()


class CreateFlowAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create a flow with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        flow_json = json.loads(data.decode('utf-8'))
        prepid = flow_controller.create(flow_json)
        return self.output_text({'response': prepid, 'success': True, 'message': ''})


class DeleteFlowAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a flow with the provided JSON content
        """
        data = flask.request.data
        flow_json = json.loads(data.decode('utf-8'))
        prepid = flow_controller.delete(flow_json)
        return self.output_text({'response': prepid, 'success': True, 'message': ''})


class UpdateFlowAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Update a flow with the provided JSON content
        """
        data = flask.request.data
        flow_json = json.loads(data.decode('utf-8'))
        prepid = flow_controller.update(flow_json)
        return self.output_text({'response': prepid, 'success': True, 'message': ''})


class GetFlowAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid):
        """
        Get a single flow with given prepid
        """
        flow = flow_controller.get(prepid)
        return self.output_text({'response': flow.get_json(), 'success': True, 'message': ''})
