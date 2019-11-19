from core.controller.controller_base import ControllerBase
from core.model.flow import Flow
from core.database.database import Database


class FlowController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)

    def __check_flow(self, flow):
        """
        Check if all attributes have valid relations and values
        This does not overlap with checks done by object setter
        """
        self.logger.debug('Checking flow %s', flow.get_prepid())
        campaign_db = Database('campaigns')
        for source_campaign_prepid in flow.get('source_campaigns'):
            if not campaign_db.document_exists(source_campaign_prepid):
                raise Exception('"%s" does not exist' % (source_campaign_prepid))

        target_campaign_prepid = flow.get('target_campaign')
        if target_campaign_prepid:
            if not campaign_db.document_exists(target_campaign_prepid):
                raise Exception('"%s" does not exist' % (target_campaign_prepid))

        return True


    def create_flow(self, flow_json):
        """
        Create a new flow
        """
        flow = Flow(json_input=flow_json)
        prepid = flow.get_prepid()

        flows_db = Database('flows')
        if flows_db.get(prepid):
            raise Exception('Flow with prepid "%s" already exists' % (prepid))

        with self.locker.get_lock(prepid):
            self.logger.info('Will create %s' % (prepid))
            if self.__check_flow(flow):
                flows_db.save(flow.json())
                return flow.json()
            else:
                self.logger.error('Error while checking flow %s', prepid)
                return None

    def delete_flow(self, flow_json):
        """
        Delete a flow
        """
        flow = Flow(json_input=flow_json)
        prepid = flow.get_prepid()

        flows_db = Database('flows')
        if not flows_db.get(prepid):
            raise Exception('Flow with prepid does not "%s" exist' % (prepid))

        flows_db.delete_object(flow.json())
        return True

    def update_flow(self, flow_json):
        """
        Update a flow with given json
        """
        new_flow = Flow(json_input=flow_json)
        prepid = new_flow.get_prepid()
        with self.locker.get_lock(prepid):
            self.logger.info('Will edit %s' % (prepid))
            flows_db = Database('flows')
            old_flow = flows_db.get(prepid)
            if not old_flow:
                raise Exception('Flow with prepid does not "%s" exist' % (prepid))

            old_flow = Flow(json_input=old_flow)
            # Move over history, so it could not be overwritten
            new_flow.set('history', old_flow.get('history'))
            new_flow.set('_rev', old_flow.get('_rev'))
            changed_values = self.get_changed_values(old_flow, new_flow)
            new_flow.add_history('update', changed_values, None)
            if self.__check_flow(new_flow):
                flows_db.save(new_flow.json())
                return new_flow.json()
            else:
                self.logger.error('Error while checking flow %s', prepid)
                return None

    def get_flow(self, flow_prepid):
        """
        Return a single flow if it exists in database
        """
        flows_db = Database('flows')
        flow_json = flows_db.get(flow_prepid)
        if flow_json:
            return Flow(json_input=flow_json)
        else:
            return None
