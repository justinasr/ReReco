from core.controller.controller_base import ControllerBase
from core.model.campaign import Campaign


class CampaignController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'campaigns'
        self.model_class = Campaign

    def check_for_create(self, obj):
        """
        Perform checks on object before adding it to database
        """
        return True

    def check_for_update(self, old_obj, new_obj):
        """
        Compare existing and updated objects to see if update is valid
        """
        return True

    def check_for_delete(self, obj):
        """
        Perform checks on object before deleting it from database
        """
        return True
