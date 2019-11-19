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
                raise Exception('Invalid key: %s' % (', '.join(bad_keys)))

        for key in keys:
            if key not in json_input:
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
            raise Exception('Attribute %s could not be found in %s schema' % (attribute,
                                                                              self.__class_name))

        if not isinstance(value, type(self.__schema[attribute])):
            expected_type = type(self.__schema[attribute]).__name__
            got_type = type(value).__name__
            raise Exception('Object %s attribute %s is wrong type. Expected %s, got %s' % (prepid,
                                                                                           attribute,
                                                                                           expected_type,
                                                                                           got_type))

        if self.check_attribute(attribute, value):
            if attribute == 'prepid':
                self.__json['_id'] = value
            elif attribute == '_id':
                self.__json['prepid'] = value

            self.__json[attribute] = value
            return self.__json
        else:
            raise Exception('Invalid value %s for key %s for object %s of type %s' % (value,
                                                                                      attribute,
                                                                                      prepid,
                                                                                      self.__class_name))

    def get(self, attribute):
        """
        Get attribute of the object
        """
        if not attribute:
            raise Exception('Attribute name not specified')

        if attribute not in self.__schema:
            raise Exception('Attribute %s does not exist in %s schema' % (attribute,
                                                                          self.__class_name))

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
        return 'Object ID: %s\nType: %s\nDict: %s\n' % (self.get_prepid(),
                                                        self.__class_name,
                                                        json.dumps(self.__json,
                                                                   indent=4,
                                                                   sort_keys=True))

    def add_history(self, action, value, user):
        history = self.get('history')
        history.append({'action': action,
                        'time': int(time.time()),
                        'value': value})
        self.set('history', history)
