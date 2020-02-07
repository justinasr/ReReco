"""
Module that contains SubcampaignController class
"""
from core.controller.controller_base import ControllerBase
from core.model.subcampaign import Subcampaign
from core.model.sequence import Sequence
from core.database.database import Database


class SubcampaignController(ControllerBase):
    """
    Controller that has all actions related to a subcampaign
    """

    def __init__(self):
        ControllerBase.__init__(self)
        self.database_name = 'subcampaigns'
        self.model_class = Subcampaign

    def get(self, prepid):
        obj = super().get(prepid)
        if obj:
            new_sequences = []
            for sequence in obj.get('sequences'):
                new_sequences.append(Sequence(json_input=sequence).get_json())

            obj.set('sequences', new_sequences)
            return obj

        return None

    def check_for_create(self, obj):
        sequences = []
        for sequence_json in obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        obj.set('sequences', sequences)
        return True

    def check_for_update(self, old_obj, new_obj, changed_values):
        sequences = []
        for sequence_json in new_obj.get('sequences'):
            sequence = Sequence(json_input=sequence_json)
            sequences.append(sequence.get_json())

        new_obj.set('sequences', sequences)
        return True

    def check_for_delete(self, obj):
        prepid = obj.get('prepid')
        requests_db = Database('requests')
        requests = requests_db.query(f'subcampaign={prepid}')
        if requests:
            raise Exception(f'It is not allowed to delete subcampaigns that have existing '
                            f'requests. {prepid} has {len(requests)} requests')

        return True

    def get_editing_info(self, obj):
        editing_info = {k: not k.startswith('_') for k in obj.get_json().keys()}
        prepid = obj.get_prepid()
        editing_info['prepid'] = not bool(prepid)
        editing_info['history'] = False
        if prepid:
            requests_db = Database('requests')
            subcampaign_requests = requests_db.query(f'subcampaign={prepid}')
            if subcampaign_requests:
                editing_info['energy'] = False
                editing_info['step'] = False
                editing_info['cmssw_release'] = False
                editing_info['sequences'] = False
                editing_info['memory'] = False

        return editing_info

    def get_default_sequence(self, subcampaign):
        """
        Return a default sequence for a subcampaign
        """
        self.logger.debug('Creating a default sequence for %s', subcampaign.get_prepid())
        sequence = Sequence()
        return sequence
