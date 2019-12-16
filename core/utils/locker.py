from threading import RLock
import logging
import threading


class Locker():

    __locks = {}

    def __init__(self, prepid=None):
        self.logger = logging.getLogger()

    def get_lock(self, prepid):
        if prepid not in self.__locks:
            self.__locks[prepid] = RLock()

        lock = self.__locks[prepid]
        self.logger.info('Returning a lock for %s. Thread %s' % (prepid,
                                                                 str(threading.current_thread())))
        return lock
