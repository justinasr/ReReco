from core.controller.controller_base import ControllerBase
from core.model.campaign import Campaign
from core.database.database import Database


class CampaignController(ControllerBase):
    def __init__(self):
        ControllerBase.__init__(self)

    def __check_campaign(self, campaign):
        """
        Check if all attributes have valid relations and values
        This does not overlap with checks done by object setter
        """
        self.logger.debug('Checking campaign %s', campaign.get_prepid())
        return True


    def create_campaign(self, campaign_json):
        """
        Create a new campaign
        """
        campaign = Campaign(json_input=campaign_json)
        prepid = campaign.get_prepid()

        campaigns_db = Database('campaigns')
        if campaigns_db.get(prepid):
            raise Exception('Campaign with prepid "%s" already exists' % (prepid))

        with self.locker.get_lock(prepid):
            self.logger.info('Will create %s' % (prepid))
            if self.__check_campaign(campaign):
                campaigns_db.save(campaign.json())
                return campaign.json()
            else:
                self.logger.error('Error while checking campaign %s', prepid)
                return None

    def delete_campaign(self, campaign_json):
        """
        Delete a campaign
        """
        campaign = Campaign(json_input=campaign_json)
        prepid = campaign.get_prepid()

        campaigns_db = Database('campaigns')
        if not campaigns_db.get(prepid):
            raise Exception('Campaign with prepid does not "%s" exist' % (prepid))

        campaigns_db.delete_object(campaign.json())
        return True

    def update_campaign(self, campaign_json):
        """
        Update a campaign with given json
        """
        new_campaign = Campaign(json_input=campaign_json)
        prepid = new_campaign.get_prepid()
        with self.locker.get_lock(prepid):
            self.logger.info('Will edit %s' % (prepid))
            campaigns_db = Database('campaigns')
            old_campaign = campaigns_db.get(prepid)
            if not old_campaign:
                raise Exception('Campaign with prepid does not "%s" exist' % (prepid))

            old_campaign = Campaign(json_input=old_campaign)
            # Move over history, so it could not be overwritten
            new_campaign.set('history', old_campaign.get('history'))
            new_campaign.set('_rev', old_campaign.get('_rev'))
            changed_values = self.get_changed_values(old_campaign, new_campaign)
            new_campaign.add_history('update', changed_values, None)
            if self.__check_campaign(new_campaign):
                campaigns_db.save(new_campaign.json())
                return new_campaign.json()
            else:
                self.logger.error('Error while checking campaign %s', prepid)
                return None

    def get_campaign(self, campaign_prepid):
        """
        Return a single campaign if it exists in database
        """
        campaigns_db = Database('campaigns')
        campaign_json = campaigns_db.get(campaign_prepid)
        if campaign_json:
            return Campaign(json_input=campaign_json)
        else:
            return None
