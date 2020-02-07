"""
Module that contains all system APIs
"""
from api.api_base import APIBase
from core.utils.request_submitter import RequestSubmitter
from core.utils.locker import Locker


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
