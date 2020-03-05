"""
Module that contains all request APIs
"""
from api.api_base import APIBase
from core.utils.settings import Settings


class SettingsAPI(APIBase):
    """
    Endpoint for getting a setting value
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, name=None):
        """
        Get a setting with given name
        """
        if name:
            setting = Settings().get(name)
        else:
            setting = Settings().get_all()

        return self.output_text({'response': setting, 'success': True, 'message': ''})
