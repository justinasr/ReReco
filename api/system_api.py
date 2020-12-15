"""
Module that contains all system APIs
"""
from core_lib.api.api_base import APIBase
from core_lib.utils.locker import Locker
from core_lib.database.database import Database
from core_lib.utils.user_info import UserInfo
from core.utils.request_submitter import RequestSubmitter


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
    @APIBase.ensure_role('administrator')
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

    def get_requests(self):
        """
        Return summary of requests by status and submitted requests by processing string
        """
        collection = Database('requests').collection
        by_status = collection.aggregate([{'$match': {'deleted': {'$ne': True}}},
                                          {'$group': {'_id': '$status',
                                                      'count': {'$sum': 1}}}])

        by_processing_string = collection.aggregate([{'$match': {'deleted': {'$ne': True}}},
                                                     {'$match': {'status': 'submitted'}},
                                                     {'$group': {'_id': '$processing_string',
                                                                 'count': {'$sum': 1}}},
                                                     {'$sort': {'count': -1}}])
        statuses = ['new', 'approved', 'submitting', 'submitted', 'done']
        by_status = sorted(list(by_status), key=lambda x: statuses.index(x['_id']))
        by_processing_string = sorted(list(by_processing_string), key=lambda x: (x['count'], x['_id'].lower()), reverse=True)
        return by_status, by_processing_string

    def get_tickets(self):
        """
        Return summary of tickets by status
        """
        collection = Database('tickets').collection
        by_status = collection.aggregate([{'$match': {'deleted': {'$ne': True}}},
                                          {'$group': {'_id': '$status',
                                                      'count': {'$sum': 1}}}])

        statuses = ['new', 'done']
        by_status = sorted(list(by_status), key=lambda x: statuses.index(x['_id']))
        return by_status

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get number of Requests with each status and processing strings of submitted requests
        """
        requests_by_status, requests_by_ps = self.get_requests()
        tickets_by_status = self.get_tickets()
        return self.output_text({'response': {'requests' : {'by_status': requests_by_status,
                                                            'by_processing_string': requests_by_ps},
                                              'tickets' : {'by_status': tickets_by_status}},
                                 'success': True,
                                 'message': ''})
