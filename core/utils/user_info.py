"""
Module that contains UserInfo class
"""
from flask import request

class UserInfo():
    """
    Class that holds information about user
    Information is obtained from headers supplied by SSO proxy
    """
    def __init__(self):
        self.__user = None

    def __get_user_dict(self):
        """
        Check request headers and parse user information
        """
        if not self.__user:
            groups = request.headers.get('Adfs-Group', '').split(';')
            groups = [x.strip() for x in groups if x.strip()]
            username = request.headers.get('Adfs-Login')
            name = request.headers.get('Adfs-Fullname')
            self.__user = {'name': name, 'username': username, 'groups': groups}

        return self.__user

    def get_username(self):
        """
        Get username, i.e. login name
        """
        return self.__get_user_dict()['username']

    def get_user_name(self):
        """
        Get user name and last name
        """
        return self.__get_user_dict()['name']

    def get_groups(self):
        """
        Get list of groups that user is member of
        """
        return self.__get_user_dict()['groups']
