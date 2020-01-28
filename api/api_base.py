"""
API base module
"""
import json
import logging
import traceback
from flask_restful import Resource
from flask import request, make_response


class APIBase(Resource):
    """
    Any object derived from APIBase should return a response dictionary with
    following structure:
    {
       'response': Object/None
       'success': True/False
       'message': String with a success message or an error (check HTTP code)
    }
    """

    def __init__(self):
        """
        Init
        """
        Resource.__init__(self)
        self.logger = logging.getLogger()

    @staticmethod
    def ensure_request_data(func):
        """
        Ensure that request has data (POST, PUT requests)
        """
        def ensure_request_data_wrapper(*args, **kwargs):
            """
            Wrapper around actual function
            """
            data = request.data
            logging.getLogger().info('Checking if data exists...')
            if not data:
                logging.getLogger().error('No data was found in request')
                return APIBase.output_text({'response': None,
                                            'success': False,
                                            'message': 'No data was found in request'},
                                           code=400)

            return func(*args, **kwargs)

        ensure_request_data_wrapper.__name__ = func.__name__
        ensure_request_data_wrapper.__doc__ = func.__doc__
        return ensure_request_data_wrapper

    @staticmethod
    def exceptions_to_errors(func):
        """
        Ensure that request has data (POST, PUT requests)
        """
        def exceptions_to_errors_wrapper(*args, **kwargs):
            """
            Wrapper around actual function
            """
            try:
                logging.getLogger().info('Wrapping call in try except...')
                return func(*args, **kwargs)
            except Exception as ex:  # pylint: disable=broad-except
                logging.getLogger().error(traceback.format_exc())
                return APIBase.output_text({'response': None,
                                            'success': False,
                                            'message': str(ex)},
                                           code=APIBase.exception_to_http_code(ex))

        exceptions_to_errors_wrapper.__name__ = func.__name__
        exceptions_to_errors_wrapper.__doc__ = func.__doc__
        return exceptions_to_errors_wrapper

    @staticmethod
    def exception_to_http_code(exception):
        """
        Convert exception to HTTP status code
        """
        if isinstance(exception, ImportError):
            return 500

        return 400

    @staticmethod
    def output_text(data, code=200, headers=None, content_type='application/json'):
        """
        Makes a Flask response with a plain text encoded body
        """
        if content_type == 'application/json':
            resp = make_response(json.dumps(data, indent=2, sort_keys=True), code)
        else:
            resp = make_response(data, code)

        resp.headers.extend(headers or {})
        resp.headers['Content-Type'] = content_type
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
