from core.database.database import Database
from core.model.model_base import ModelBase
from core.utils.locker import Locker


class ControllerBase():
    """
    Controller base class implements simple create, read, update, delete methods
    as well as some convenience methods such as get_changed_values for update
    This is a base class for all controllers
    It requires database name and class object of model
    """

    def __init__(self):
        self.logger = ModelBase._ModelBase__logger
        self.locker = Locker()
        self.database_name = None
        self.model_class = None

    def create(self, json_data):
        """
        Create a new object from given json_data
        """
        new_object = self.model_class(json_input=json_data)
        prepid = new_object.get_prepid()

        database = Database(self.database_name)
        if database.get(prepid):
            raise Exception(f'Object with prepid "{prepid}" already exists in {self.database_name} database')

        with self.locker.get_lock(prepid):
            self.logger.info('Will create %s', (prepid))
            new_object.add_history('create', prepid, None)
            if self.check_for_create(new_object):
                database.save(new_object.get_json())
                return new_object.get_json()
            else:
                self.logger.error('Error while checking new item %s', prepid)
                return None

    def get(self, prepid):
        """
        Return a single object if it exists in database
        """
        database = Database(self.database_name)
        object_json = database.get(prepid)
        if object_json:
            return self.model_class(json_input=object_json)
        else:
            return None

    def update(self, json_data):
        """
        Update a single object with given json
        """
        new_object = self.model_class(json_input=json_data)
        prepid = new_object.get_prepid()
        with self.locker.get_lock(prepid):
            self.logger.info('Will edit %s', prepid)
            database = Database(self.database_name)
            old_object = database.get(prepid)
            if not old_object:
                raise Exception(f'Object with prepid "{prepid}" does not exist in {self.database_name} database')

            old_object = self.model_class(json_input=old_object)
            # Move over history, so it could not be overwritten
            new_object.set('history', old_object.get('history'))
            self.before_update(new_object)
            changed_values = self.get_changes(old_object, new_object)
            if not changed_values:
                # Nothing was updated
                self.logger.info('Nothing was updated for %s', prepid)
                return old_object.get_json()

            self.edit_allowed(old_object, changed_values)
            new_object.add_history('update', changed_values, None)
            if self.check_for_update(old_object, new_object, changed_values):
                database.save(new_object.get_json())
                return new_object.get_json()
            else:
                self.logger.error('Error while updating %s', prepid)
                return None

    def delete(self, json_data):
        """
        Delete a single object
        """
        prepid = json_data.get('prepid', None)
        database = Database(self.database_name)
        json_data = database.get(prepid)
        if not json_data:
            raise Exception(f'Object with prepid "{prepid}" does not exist in {self.database_name} database')

        obj = self.model_class(json_input=json_data)
        with self.locker.get_lock(prepid):
            self.logger.info('Will delete %s', (prepid))
            self.before_delete(obj)
            if self.check_for_delete(obj):
                database.delete_document(obj.get_json())
                return {'prepid': prepid}
            else:
                self.logger.error('Error while deleting %s', prepid)
                return None

    def check_for_create(self, obj):
        """
        Perform checks on object before adding it to database
        """
        raise NotImplementedError('This method must be implemented')

    def check_for_update(self, old_obj, new_obj):
        """
        Compare existing and updated objects to see if update is valid
        """
        raise NotImplementedError('This method must be implemented')

    def check_for_delete(self, obj):
        """
        Perform checks on object before deleting it from database
        """
        raise NotImplementedError('This method must be implemented')

    def before_create(self, obj):
        """
        Actions to be performed before object is updated
        """
        pass

    def before_update(self, obj):
        """
        Actions to be performed before object is updated
        """
        pass

    def before_delete(self, obj):
        """
        Actions to be performed before object is deleted
        """
        pass

    def get_editing_info(self, obj):
        """
        Return a dictionary of pairs where key is attribute name and value is
        a boolean whether that attribute can be edited, for example
        {
          "prepid": False,
          "notes": True
        }
        """
        raise NotImplementedError('This method must be implemented')

    def edit_allowed(self, obj, changed_values):
        """
        Check whether done edit is allowed based on editing info
        and changed values
        """
        editing_info = self.get_editing_info(obj)
        if not editing_info:
            return True

        def recursive_edit_allowed(editing_info, changed_values):
            if isinstance(editing_info, bool):
                return editing_info

            elif isinstance(changed_values, dict):
                for key, value in changed_values.items():
                    allowed = recursive_edit_allowed(editing_info.get(key, False), value)
                    if not allowed:
                        raise Exception(f'It is not allowed to edit {key}')

            elif isinstance(changed_values, list):
                for i in range(len(changed_values)):
                    allowed = recursive_edit_allowed(editing_info.get(key, False), value)
                    if not allowed:
                        return False

            return True

        self.logger.info(editing_info)
        recursive_edit_allowed(editing_info, changed_values)
        return True

    def get_changes(self, reference, target):
        """
        Get dictionary of changed attributes
        """
        if isinstance(reference, ModelBase) and isinstance(reference, ModelBase):
            # Compare two ReReco objects
            changed_values = {}
            schema = reference.schema()
            schema_keys = set(schema.keys())
            schema_keys.remove('history')
            for key in schema_keys:
                reference_value = reference.get(key)
                target_value = target.get(key)
                changed = self.get_changes(reference_value, target_value)
                if isinstance(changed, bool):
                    if changed:
                        changed_values[key] = changed
                else:
                    changed_values[key] = changed

            return changed_values
        elif isinstance(reference, dict) and isinstance(target, dict):
            changed_values = {}
            keys = reference.keys()
            for key in keys:
                reference_value = reference.get(key)
                target_value = target.get(key)
                changed = self.get_changes(reference_value, target_value)
                if isinstance(changed, bool):
                    if changed:
                        changed_values[key] = changed
                else:
                    changed_values[key] = changed

            if changed_values:
                return changed_values

        elif isinstance(reference, list) and isinstance(target, list):
            if len(reference) != len(target):
                return True

            changed_values = []
            for i in range(len(reference)):
                changed_values.append(self.get_changes(reference[i], target[i]))

            for changed in changed_values:
                if changed:
                    return changed_values

        else:
            return reference != target

        return False
