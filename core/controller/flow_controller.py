from core.controller.controller_base import ControllerBase
from core.model.flow import Flow
from core.database.database import Database


class FlowController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'flows'
        self.model_class = Flow

    def check_for_create(self, obj):
        """
        Perform checks on object before adding it to database
        """
        self.logger.debug('Checking flow %s', obj.get_prepid())
        campaign_db = Database('campaigns')
        for source_campaign_prepid in obj.get('source_campaigns'):
            if not campaign_db.document_exists(source_campaign_prepid):
                raise Exception('"%s" does not exist' % (source_campaign_prepid))

        target_campaign_prepid = obj.get('target_campaign')
        if target_campaign_prepid:
            if not campaign_db.document_exists(target_campaign_prepid):
                raise Exception('"%s" does not exist' % (target_campaign_prepid))

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
