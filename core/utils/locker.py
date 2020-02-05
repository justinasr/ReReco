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
    __infos = {}
    __locker_lock = RLock()

    def __init__(self):
        self.logger = logging.getLogger()

    def get_nonblocking_lock(self, prepid, info=''):
        lock = self.get_lock(prepid, info)
        # If we do a plus one
        if not lock.acquire(blocking=False):
            raise LockedException()

        # We have to subtract one
        lock.release()
        return lock

    def get_lock(self, prepid, info=''):
        """
        Return a lock for a given prepid
        It can be either existing one or a new one will be created
        """
        with Locker.__locker_lock:
            lock = self.__locks.get(prepid, RLock())
            self.__locks[prepid] = lock
            self.__infos[prepid] = info

        self.logger.debug('Returning a lock for %s. Thread %s',
                          prepid,
                          str(current_thread()))

        return lock

    def get_status(self):
        return {k: {'l': str(v), 'i': self.__infos[k]} for k, v in self.__locks.items()}


class LockedException(Exception):
    pass
