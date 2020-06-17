"""
Module that contains ModelBase class
"""
import json
import logging
import re
import time
from copy import deepcopy
from core.utils.user_info import UserInfo
from core.utils.exceptions import BadAttribute


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
    __cmssw_regex = 'CMSSW_[0-9]{1,3}_[0-9]{1,3}_[0-9]{1,3}.{0,20}'  # CMSSW_ddd_ddd_ddd[_XXX...]
    __dataset_regex = '^/[a-zA-Z0-9\\-_]{1,99}/[a-zA-Z0-9\\.\\-_]{1,199}/[A-Z\\-]{1,50}$'
    __subcampaign_regex = '[a-zA-Z0-9]{1,25}\\-[a-zA-Z0-9_]{1,35}'
    default_lambda_checks = {
        'cmssw_release': lambda cmssw: ModelBase.matches_regex(cmssw, ModelBase.__cmssw_regex),
        'dataset': lambda ds: ModelBase.matches_regex(ds, ModelBase.__dataset_regex),
        'energy': lambda energy: 0 <= energy <= 100,
        'memory': lambda mem: 0 <= mem <= 64000,
        'processing_string': lambda ps: ModelBase.matches_regex(ps, '[a-zA-Z0-9_]{1,100}'),
        'priority': lambda priority: 20000 <= priority <= 1000000,
        'scram_arch': lambda sa: ModelBase.matches_regex(sa, '[a-z0-9_]{0,30}'),
        'subcampaign': lambda sc: ModelBase.matches_regex(sc, ModelBase.__subcampaign_regex),
    }
    lambda_checks = {}

    def __init__(self, json_input=None):
        self.initialized = False
        self.__json = {}
        self.logger = ModelBase.__logger
        self.__class_name = self.__class__.__name__
        self.__fill_values(json_input)
        self.initialized = True

    def __fill_values(self, json_input):
        """
        Copy values from given dictionary to object's json
        Initialize default values from schema if any are missing
        """
        if json_input:
            if 'prepid' in self.__schema or '_id' in self.__schema:
                prepid = json_input.get('prepid')
                if not prepid:
                    raise BadAttribute('PrepID cannot be empty')

                self.set('prepid', prepid)

        else:
            json_input = {}

        ignore_keys = set(['_id', 'prepid'])
        keys = set(self.__schema.keys())
        if json_input:
            # Show errors if any incorrect keys are passed
            bad_keys = set(json_input.keys()) - keys - ignore_keys
            if bad_keys:
                bad_keys = [str(key) for key in bad_keys]
                self.logger.warning('Keys that are not in schema of %s: %s',
                                    self.__class_name,
                                    ', '.join(bad_keys))

        for key in keys - ignore_keys:
            if key not in json_input:
                self.__json[key] = deepcopy(self.__schema[key])
            else:
                self.set(key, json_input[key])

    def set(self, attribute, value=None):
        """
        Set attribute of the object
        """
        prepid = self.get_prepid()
        if not prepid:
            prepid = self.__class_name

        if not attribute:
            raise BadAttribute('Attribute name not specified')

        if attribute not in self.__schema:
            raise BadAttribute(f'Attribute {attribute} could not be '
                               f'found in {self.__class_name} schema')

        # Check value type and cast if needed
        expected_type = type(self.__schema[attribute])
        if not isinstance(value, expected_type):
            self.logger.debug('%s of %s is not expected type. Expected %s, got %s. Try to cast',
                              attribute,
                              prepid,
                              expected_type,
                              type(value))
            value = self.cast_value_to_correct_type(attribute, value)

        if not self.check_attribute(attribute, value):
            self.logger.error('Invalid value "%s" for key "%s" for object %s of type %s',
                              value,
                              attribute,
                              prepid,
                              self.__class_name)
            raise BadAttribute(f'Invalid {attribute} value {value} for {prepid}')

        self.__json[attribute] = value
        if attribute == 'prepid':
            self.__json['_id'] = value

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
        First it tries to find exact name match in lambda functions
        Then it checks for lambda function with double underscore prefix which
        indicates that this is a list of values
        """
        if attribute_name in self.lambda_checks:
            self.logger.debug('Checking %s of %s', attribute_name, self.__class_name)
            if not self.lambda_checks[attribute_name](attribute_value):
                return False

        # List
        if f'__{attribute_name}' in self.lambda_checks:
            if not isinstance(attribute_value, list):
                raise Exception(f'Expected {attribute_name} to be a list')

            self.logger.debug('Checking %s elements of %s', attribute_name, self.__class_name)
            lambda_check = self.lambda_checks[f'__{attribute_name}']
            for item in attribute_value:
                if not lambda_check(item):
                    raise Exception(f'Bad {attribute_name} value "{item}"')

        # Dict
        if f'_{attribute_name}' in self.lambda_checks:
            if not isinstance(attribute_value, dict):
                raise Exception(f'Expected {attribute_name} to be a dict')

            lambda_checks = self.lambda_checks[f'_{attribute_name}']
            invalid_keys = set(attribute_value.keys()) - set(lambda_checks.keys())
            if invalid_keys:
                raise Exception(f'Keys {",".join(invalid_keys)} are not '
                                f'allowed in {attribute_name}')

            for key, lambda_check in lambda_checks.items():
                self.logger.debug('Checking %s.%s of %s', attribute_name, key, self.__class_name)
                if not lambda_check(attribute_value[key]):
                    raise Exception(f'Bad {key} value "{item}" in {attribute_name} dictionary')

        return True

    def cast_value_to_correct_type(self, attribute_name, attribute_value):
        """
        If value is not correct type, try to cast it to
        correct type according to schema
        """
        expected_type = type(self.__schema[attribute_name])
        got_type = type(attribute_value)
        if expected_type == list and got_type == str:
            return [x.strip() for x in attribute_value.split(',') if x.strip()]

        prepid = self.get_prepid()
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

    def __get_json(self, item):
        """
        Internal method to recursively create dict representations of objects
        """
        if isinstance(item, ModelBase):
            return item.get_json()

        if isinstance(item, list):
            new_list = []
            for element in item:
                new_list.append(self.__get_json(element))

            return new_list

        return item

    def get_json(self):
        """
        Return JSON of the object
        """
        built_json = {}
        for attribute, value in self.__json.items():
            built_json[attribute] = self.__get_json(value)

        return deepcopy(built_json)

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
        object_json = self.get_json()
        if 'history' in object_json:
            del object_json['history']

        return (f'Object ID: {self.get_prepid()}\n'
                f'Type: {self.__class_name}\n'
                f'Dict: {json.dumps(object_json, indent=2, sort_keys=True)}')

    def add_history(self, action, value, user, timestamp=None):
        """
        Add entry to object's history
        If no time is specified, use current time
        """
        if user is None:
            user = UserInfo().get_username()

        history = self.get('history')
        history.append({'action': action,
                        'time': int(timestamp if timestamp else time.time()),
                        'user': user,
                        'value': value})
        self.set('history', history)

    @staticmethod
    def lambda_check(name):
        """
        Return a lambda check from default lambda checks dictionary
        """
        return ModelBase.default_lambda_checks.get(name)
