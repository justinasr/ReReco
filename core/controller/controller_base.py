from core.model.model_base import ModelBase
from core.utils.locker import Locker


class ControllerBase():
    def __init__(self):
        self.logger = ModelBase._ModelBase__logger
        self.locker = Locker()

    def get_changed_values(self, reference, target, prefix='', changed_values=None):
        schema = reference.schema()
        schema_keys = schema.keys()
        if changed_values is None:
            changed_values = {}

        for key in schema_keys:
            type_in_schema = type(schema.get(key))
            key_with_prefix = prefix + ('.' if prefix else '') + key
            if type_in_schema == dict:
                self.get_changed_values(reference.get(key),
                                        target.get(key),
                                        key_with_prefix,
                                        changed_values)
            elif type_in_schema == list:
                pass
            else:
                if reference.get(key) != target.get(key):
                    changed_values[key_with_prefix] = target.get(key)

        return changed_values
