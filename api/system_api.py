"""
Module that contains all system APIs
"""
from api.api_base import APIBase
from core.utils.request_submitter import RequestSubmitter
from core.utils.locker import Locker
from core.utils.user_info import UserInfo
from core.database.database import Database


class SubmissionWorkerStatusAPI(APIBase):
    """
    Endpoint for getting submission workers status
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get status of all request submission workers
        """
        status = RequestSubmitter().get_worker_status()
        return self.output_text({'response': status, 'success': True, 'message': ''})


class SubmissionQueueAPI(APIBase):
    """
    Endpoint for getting names in submission queue
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get status of all request submission workers
        """
        status = RequestSubmitter().get_names_in_queue()
        return self.output_text({'response': status, 'success': True, 'message': ''})


class LockerStatusAPI(APIBase):
    """
    Endpoint for getting status of all locks in the system
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get status of all locks in the system
        """
        status = Locker().get_status()
        return self.output_text({'response': status, 'success': True, 'message': ''})


class UserInfoAPI(APIBase):
    """
    Endpoint for getting user information
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get status of all locks in the system
        """
        user_info = UserInfo().get_user_info()
        return self.output_text({'response': user_info, 'success': True, 'message': ''})


class ObjectsInfoAPI(APIBase):
    """
    Endpoint for getting database information
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get number of requests with each status and processing strings of submitted requests
        """
        request_db = Database('requests')
        by_status = request_db.db.aggregate([{'$group': {'_id': '$status',
                                                         'count': {'$sum': 1}}}])

        by_processing_string = request_db.db.aggregate([{'$match': {'status': 'submitted'}},
                                                        {'$group': {'_id': '$processing_string',
                                                                    'count': {'$sum': 1}}},
                                                        {'$sort': {'count': -1}}])

        statuses = ['new', 'approved', 'submitting', 'submitted', 'done']
        by_status = sorted(list(by_status), key=lambda x: statuses.index(x['_id']))
        by_processing_string = list(by_processing_string)
        return self.output_text({'response': {'by_status': by_status,
                                              'by_processing_string': by_processing_string},
                                 'success': True,
                                 'message': ''})
