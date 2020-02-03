"""
Module that contains all system APIs
"""
from api.api_base import APIBase
from core.utils.request_submitter import RequestSubmitter


class SubmissionWorkerStatusAPI(APIBase):
    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Create a flow with the provided JSON content. Requires a unique prepid
        """
        status = RequestSubmitter().get_worker_status()
        return self.output_text({'response': status, 'success': True, 'message': ''})
