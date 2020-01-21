"""
Module that contains ModelBase class
"""
import json
import logging
import re
import time
from copy import deepcopy


class ModelBase():
    """
    Base class for all ReReco objects in the system
    Has some convenience methods as well as somewhat smart setter
    Contains a bunch of sanity checks
    """
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
        if json_input:
            prepid = json_input.get('prepid')
            if not prepid and ('prepid' in self.__schema or '_id' in self.__schema):
                raise Exception('PrepID cannot be empty')

            if self.check_attribute('prepid', prepid):
                if 'prepid' in self.__schema:
                    self.__json['prepid'] = prepid

                if '_id' in self.__schema:
                    self.__json['_id'] = prepid
            else:
                self.logger.error('Invalid prepid %s for %s', prepid, self.__class_name)
                raise Exception(f'Invalid prepid {prepid} for {self.__class_name}')

            if '_rev' in self.__schema and '_rev' in json_input:
                self.__json['_rev'] = json_input['_rev']
        else:
            json_input = {}

        ignore_keys = set(['_id', '_rev', 'prepid'])
        keys = set(self.__schema.keys())
        if json_input:
            # Just to show errors if any incorrect keys are passed
            bad_keys = set(json_input.keys()) - keys - ignore_keys
            if bad_keys:
                raise Exception(f'Invalid key "{", ".join(bad_keys)}" for {self.__class_name}')

        for key in keys - ignore_keys:
            if key not in json_input:
                self.__json[key] = deepcopy(self.__schema[key])
            else:
                self.set(key, json_input[key])

        self.logger.debug('%s\n', str(self))

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
            raise Exception(f'Attribute {attribute} could not be '
                            f'found in {self.__class_name} schema')

        if attribute in ('prepid', '_id'):
            raise Exception('Changing prepid or _id is not allowed')

        if not isinstance(value, type(self.__schema[attribute])):
            self.logger.debug('%s of %s is not expected (%s) type (got %s). Will try to cast',
                              attribute,
                              prepid,
                              type(self.__schema[attribute]),
                              type(value))
            value = self.cast_value_to_correct_type(attribute, value)

        value = self.before_attribute_check(attribute, value)
        if not self.check_attribute(attribute, value):
            self.logger.error('Invalid value "%s" for key "%s" for object %s of type %s',
                              value,
                              attribute,
                              prepid,
                              self.__class_name)
            raise Exception(f'Invalid {attribute} value {value} for {prepid}')

        self.__json[attribute] = value
        return self.__json

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

        if '_id' in self.__json:
            return self.__json['_id']

        return None

    def check_attribute(self, attribute_name, attribute_value):
        """
        This method must return whether given value of attribute is valid
        or raise exception with error
        """
        raise NotImplementedError('This method must be implemented')

    def cast_value_to_correct_type(self, attribute_name, attribute_value):
        """
        If value is not correct type, try to cast it to
        correct type according to schema
        """
        prepid = self.get_prepid()
        expected_type = type(self.__schema[attribute_name])
        got_type = type(attribute_value)
        expected_type_name = expected_type.__name__
        got_type_name = got_type.__name__
        try:
            return expected_type(attribute_value)
        except Exception as ex:
            self.logger.error(ex)
            raise Exception(f'Object {prepid} attribute {attribute_name} is wrong type. '
                            f'Expected {expected_type_name}, got {got_type_name}. '
                            f'It cannot be automatically casted to correct type')

    @classmethod
    def matches_regex(cls, value, regex):
        """
        Check if given string fully matches given regex
        """
        matcher = re.compile(regex)
        match = matcher.fullmatch(value)
        if match:
            return True

        return False

    def get_json(self):
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
        return (f'Object ID: {self.get_prepid()}\n'
                f'Type: {self.__class_name}\n'
                f'Dict: {json.dumps(self.__json, indent=4, sort_keys=True)}\n')

    def add_history(self, action, value, user, timestamp=None):
        """
        Add entry to object's history
        If no time is specified, use current time
        """
        history = self.get('history')
        history.append({'action': action,
                        'time': int(timestamp if timestamp else time.time()),
                        'user': user,
                        'value': value})
        self.set('history', history)

    def before_attribute_check(self, attribute_name, attribute_value):
        """
        Preprocess value if needed before performing checks setting it
        This should include sanitization and whitespace removal (stripping)
        """
        self.logger.debug('Returning default %s value %s', attribute_name, attribute_value)
        return attribute_value
