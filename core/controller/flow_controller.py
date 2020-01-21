"""
Module that contains FlowController class
"""
from core.controller.controller_base import ControllerBase
from core.model.flow import Flow
from core.database.database import Database


class FlowController(ControllerBase):
    """
    Controller that has all actions related to a flow
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'flows'
        self.model_class = Flow

    def check_for_create(self, obj):
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

    def check_for_update(self, old_obj, new_obj, changed_values):
        return True

    def check_for_delete(self, obj):
        return True

    def get_editing_info(self, obj):
        editing_info = {k: not k.startswith('_') for k in obj.get_json().keys()}
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
        return editing_info
