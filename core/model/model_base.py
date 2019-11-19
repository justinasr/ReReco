import json
import logging
import re
import time
from copy import deepcopy


class ModelBase():
    __json = {}
    __schema = {}
    __model_name = None
    __logger = logging.getLogger()
    __class_name = None

    def __init__(self, json_input=None):
        self.__json = {}
        self.logger = ModelBase.__logger
        self.__class_name = self.__class__.__name__

        self.logger.debug('Creating %s object. Json input present: %s',
                          self.__class_name,
                          'YES' if json_input else 'NO')
        self.__fill_values(json_input)

    def __fill_values(self, json_input):
        """
        Copy values from given dictionary to object's json
        Initialize default values from schema if any are missing
        """
        keys = set(self.__schema.keys())
        if json_input:
            # Just to show errors if any incorrect keys are passed
            bad_keys = set(json_input.keys()) - keys - (set(['_id', '_rev']))
            if bad_keys:
                raise Exception(f'Invalid key: {", ".join(bad_keys)}')

        for key in keys:
            if key == '_id':
                # Do not do anything for _id, it will be set
                # together with prepid
                continue
            elif key == 'prepid':
                # Special case for prepid
                self.__json['prepid'] = self.check_attribute('prepid', json_input[key])
                self.__json['_id'] = self.__json['prepid']
            elif key not in json_input:
                self.__json[key] = deepcopy(self.__schema[key])
            else:
                self.set(key, json_input[key])

    def set(self, attribute, value=None):
        """
        Set attribute of the object
        """
        prepid = self.get_prepid()
        self.logger.debug('Setting %s and value %s for %s of type %s',
                          attribute,
                          value,
                          prepid,
                          self.__class_name)

        if not attribute:
            raise Exception('Attribute name not specified')

        if attribute not in self.__schema:
            raise Exception(f'Attribute {attribute} could not be found in {self.__class_name} schema')

        if attribute == 'prepid' or attribute == '_id':
            raise Exception('Changing prepid or _id is not allowed')

        if not isinstance(value, type(self.__schema[attribute])):
            expected_type = type(self.__schema[attribute]).__name__
            got_type = type(value).__name__
            raise Exception(f'Object {prepid} attribute {attribute} is wrong type. Expected {expected_type}, got {got_type}')

        if self.check_attribute(attribute, value):
            self.__json[attribute] = value
            return self.__json
        else:
            raise Exception(f'Invalid value {value} for key {attribute} for object {prepid} of type {self.__class_name}')

    def get(self, attribute):
        """
        Get attribute of the object
        """
        if not attribute:
            raise Exception('Attribute name not specified')

        if attribute not in self.__schema:
            raise Exception(f'Attribute {attribute} does not exist in {self.__class_name} schema')

        return self.__json[attribute]

    def get_prepid(self):
        """
        Return prepid or _id if any of it exist
        Return none if it doesn't
        """
        if 'prepid' in self.__json:
            return self.__json['prepid']
        elif '_id' in self.__json:
            return self.__json['_id']

        return None

    def check_attribute(self, attribute_name, attribute_value):
        """
        This method should be overwritten in child classes and
        check whether given value of attribute is valid
        """
        return True

    @classmethod
    def matches_regex(cls, value, regex):
        matcher = re.compile(regex)
        match = matcher.fullmatch(value)
        if match:
            return True

        return False

    def json(self):
        """
        Return JSON of the object
        """
        return deepcopy(self.__json)

    @classmethod
    def schema(cls):
        """
        Return a copy of scema
        """
        return deepcopy(cls.__schema)

    def __str__(self):
        """
        String representation of the object
        """
        return f'Object ID: {self.get_prepid()}\nType: {self.__class_name}\nDict: {json.dumps(self.__json, indent=4, sort_keys=True)}\n'

    def add_history(self, action, value, user, timestamp=None):
        """
        Add entry to object's history
        If no time is specified, use current time
        """
        history = self.get('history')
        history.append({'action': action,
                        'time': int(timestamp if timestamp else time.time()),
                        'value': value})
        self.set('history', history)
