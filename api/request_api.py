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
    @APIBase.ensure_role('manager')
    def put(self):
        """
        Create a request with the provided JSON content. Requires a unique prepid
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        obj = request_controller.create(request_json)
        return self.output_text({'response': obj.get_json(), 'success': True, 'message': ''})


class DeleteRequestAPI(APIBase):
    """
    Endpoint for deleting one or multiple requests
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def delete(self):
        """
        Delete a request with the provided JSON content
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        if isinstance(request_json, dict):
            results = request_controller.delete(request_json)
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                results.append(request_controller.delete(single_request_json))
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})


class UpdateRequestAPI(APIBase):
    """
    Endpoint for updating a request
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
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


class GetCMSDriverAPI(APIBase):
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


class GetConfigUploadAPI(APIBase):
    """
    Endpoint for getting a bash script to upload configs to ReqMgr config cache
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a text file with request's cmsDriver.py commands
        """
        request = request_controller.get(prepid)
        commands = request_controller.get_config_upload_file(request)
        return self.output_text(commands, content_type='text/plain')


class GetRequestJobDictAPI(APIBase):
    """
    Endpoint for getting a dictionary with job information for ReqMgr2
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, prepid=None):
        """
        Get a text file with ReqMgr2's dictionary
        """
        request = request_controller.get(prepid)
        dict_string = json.dumps(request_controller.get_job_dict(request),
                                 indent=2,
                                 sort_keys=True)
        return self.output_text(dict_string, content_type='text/plain')


class RequestNextStatus(APIBase):
    """
    Endpoint for moving one or multiple requests to next status
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self, prepid=None):
        """
        Move one or multiple requests to next status
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        if isinstance(request_json, dict):
            prepid = request_json.get('prepid')
            request = request_controller.get(prepid)
            results = request_controller.next_status(request)
            results = results.get_json()
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                prepid = single_request_json.get('prepid')
                request = request_controller.get(prepid)
                results.append(request_controller.next_status(request))

            results = [x.get_json() for x in results]
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})


class RequestPreviousStatus(APIBase):
    """
    Endpoint for moving one or multiple requests to previous status
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self, prepid=None):
        """
        Move one or multiple requests to previous status
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        if isinstance(request_json, dict):
            prepid = request_json.get('prepid')
            request = request_controller.get(prepid)
            results = request_controller.previous_status(request)
            results = results.get_json()
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                prepid = single_request_json.get('prepid')
                request = request_controller.get(prepid)
                results.append(request_controller.previous_status(request))

            results = [x.get_json() for x in results]
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})


class GetRequestRunsAPI(APIBase):
    """
    Endpoint for getting intersection of input dataset runs and runs from certification JSON
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def get(self, prepid=None):
        """
        Get a list of run numbers
        """
        request = request_controller.get(prepid)
        result = request_controller.get_runs_for_request(request)
        return self.output_text({'response': result, 'success': True, 'message': ''})


class UpdateRequestWorkflowsAPI(APIBase):
    """
    Endpoint for trigerring one or multiple request update from Stats2 (ReqMgr2 + DBS)
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Pull workflows from Stats2 (ReqMgr2 + DBS) and update request with that information
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        if isinstance(request_json, dict):
            prepid = request_json.get('prepid')
            request = request_controller.get(prepid)
            results = request_controller.update_workflows(request)
            results = results.get_json()
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                prepid = single_request_json.get('prepid')
                request = request_controller.get(prepid)
                results.append(request_controller.update_workflows(request))

            results = [x.get_json() for x in results]
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})


class RequestOptionResetAPI(APIBase):
    """
    Endpoint for rewriting request values from subcampaign
    """

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self, prepid=None):
        """
        Rewrite memory, sequences and energy from subcampaign for one or multiple requests
        """
        data = flask.request.data
        request_json = json.loads(data.decode('utf-8'))
        if isinstance(request_json, dict):
            prepid = request_json.get('prepid')
            request = request_controller.get(prepid)
            results = request_controller.option_reset(request)
            results = results.get_json()
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                prepid = single_request_json.get('prepid')
                request = request_controller.get(prepid)
                results.append(request_controller.option_reset(request))

            results = [x.get_json() for x in results]
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})
