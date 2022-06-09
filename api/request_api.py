"""
Module that contains all request APIs
"""
import json
import flask
from core_lib.api.api_base import APIBase
from core_lib.utils.common_utils import clean_split
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
        if isinstance(request_json, dict):
            results = request_controller.update(request_json)
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                results.append(request_controller.update(single_request_json))
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})


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
        args = flask.request.args
        obj = request_controller.get(prepid, args.get('deleted', '').lower() == 'true')
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
        Get an object and it's editing info or list of objects and their editing infos
        """
        if prepid:
            prepid = clean_split(prepid, ',')
            if len(prepid) == 1:
                # Return one object if there is only one prepid
                request = request_controller.get(prepid[0])
                editing_info = request_controller.get_editing_info(request)
                request = request.get_json()
            else:
                # Return a list if there are multiple prepids
                request = [request_controller.get(p) for p in prepid]
                editing_info = [request_controller.get_editing_info(r) for r in request]
                request = [r.get_json() for r in request]

        else:
            request = Request()
            editing_info = request_controller.get_editing_info(request)
            request = request.get_json()

        return self.output_text({'response': {'object': request,
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
        for_submission = flask.request.args.get('submission', '').lower() == 'true'
        commands = request_controller.get_cmsdriver(request, for_submission)
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
    def get(self, prepid):
        """
        Get a list of run numbers
        """
        request = request_controller.get(prepid)
        result = request_controller.get_runs_for_request(request)
        return self.output_text({'response': result, 'success': True, 'message': ''})

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Get a dictionary of runs and lumisection ranges for provided dataset and subcampaign
        """
        data = flask.request.data
        data_json = json.loads(data.decode('utf-8'))
        input_dataset = data_json['input_dataset']
        subcampaign_name = data_json['subcampaign']
        result = request_controller.get_runs(subcampaign_name, input_dataset)
        return self.output_text({'response': result, 'success': True, 'message': ''})


class GetRequestLumisectionsAPI(APIBase):
    """
    Endpoint for getting a subset of DCS dictionary for given request of provided runs
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def get(self, prepid):
        """
        Get a dictionary of runs and lumisection ranges for request's runs
        """
        request = request_controller.get(prepid)
        result = request_controller.get_lumisections_for_request(request)
        return self.output_text({'response': result, 'success': True, 'message': ''})

    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('manager')
    def post(self):
        """
        Get a dictionary of runs and lumisection ranges for provided runs and subcampaign
        """
        data = flask.request.data
        data_json = json.loads(data.decode('utf-8'))
        runs = data_json['runs']
        subcampaign_name = data_json['subcampaign']
        result = request_controller.get_lumisections(subcampaign_name, runs)
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
            results = request_controller.option_reset(prepid)
            results = results.get_json()
        elif isinstance(request_json, list):
            results = []
            for single_request_json in request_json:
                prepid = single_request_json.get('prepid')
                results.append(request_controller.option_reset(prepid))

            results = [x.get_json() for x in results]
        else:
            raise Exception('Expected a single request dict or a list of request dicts')

        return self.output_text({'response': results, 'success': True, 'message': ''})
