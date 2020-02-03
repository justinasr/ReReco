"""
Module that contains Locker class
"""
from threading import RLock, current_thread
import logging


class Locker():
    """
    Locker objects has a shared dictionary with locks in it
    Dictionary keys are strings
    """

    __locks = {}

    def __init__(self):
        self.logger = logging.getLogger()

    def get_nonblocking_lock(self, prepid):
        lock = self.get_lock(prepid)
        if not lock.acquire(blocking=False):
            raise LockedException()

        return lock

    def get_lock(self, prepid):
        """
        Return a lock for a given prepid
        It can be either existing one or a new one will be created
        """
        if prepid not in self.__locks:
            self.__locks[prepid] = RLock()

        lock = self.__locks[prepid]
        self.logger.debug('Returning a lock for %s. Thread %s',
                          prepid,
                          str(current_thread()))
        return lock


class LockedException(Exception):
    pass
