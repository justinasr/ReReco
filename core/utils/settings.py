"""
Module that contains Settings class
"""
from core.database.database import Database


class Settings:
    def __init__(self):
        self.database = Database('settings')

    def get_all(self):
        return self.database.query(limit=self.database.get_count())

    def get(self, setting_name):
        return self.database.get(setting_name).get('value')
