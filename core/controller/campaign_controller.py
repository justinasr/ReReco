from core.controller.controller_base import ControllerBase
from core.model.campaign import Campaign
from core.model.sequence import Sequence


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

    def check_for_update(self, old_obj, new_obj, changed_values):
        """
        Compare existing and updated objects to see if update is valid
        """
        return True

    def check_for_delete(self, obj):
        """
        Perform checks on object before deleting it from database
        """
        if obj.get('prepid') == 'RunIIFall18GS':
            raise Exception('Cannot delete this campaign for hardcoded testing reasons')

        return True

    def before_create(self, obj):
        sequences = []
        for sequence_json in obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        obj.set('sequences', sequences)

    def before_update(self, obj):
        sequences = []
        for sequence_json in obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        obj.set('sequences', sequences)

    def get_editing_info(self, campaign):
        editing_info = {k: not k.startswith('_') for k in campaign.get_json().keys()}
        editing_info['prepid'] = not bool(editing_info.get('prepid'))
        editing_info['history'] = False
        return editing_info

    def get_default_sequence(self, campaign):
        sequence = Sequence()
        return sequence
