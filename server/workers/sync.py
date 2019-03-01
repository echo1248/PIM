# -*- coding: utf-8 -*-
# File   @ sync.py
# Create @ 2019/2/26 10:19
# Author @ 819070918@qq.com


import os
import errno
import server.workers.base as base


class StopWaiting(Exception):
    """ exception raised to stop waiting for a connnection """


class SyncWorker(base.Worker):

    BUF_SIZE = 1024

    def sendto(self, data, client):
        listener = self.sockets[0]
        listener.sendto(data, client)

    def recvfrom(self, listener):
        data, client = listener.recvfrom(self.BUF_SIZE)
        self.handle(data, client)

    def is_parent_alive(self):
        if self.ppid != os.getppid():
            self.log.info("Parent changed, shutting down: %s", self)
            return False
        return True

    def run(self):

        for s in self.sockets:
            s.setblocking(0)

        self.run_for_one()

    def run_for_one(self):
        listener = self.sockets[0]
        while self.alive:

            if not self.is_parent_alive():
                return

            try:
                self.recvfrom(listener)
            except EnvironmentError as e:
                if e.errno not in (errno.EAGAIN, errno.ECONNABORTED,
                                   errno.EWOULDBLOCK):
                    raise

    def handle(self, data, client):
        try:
            respiter = self.middleware(data, client)
            # respiter.sendto(data)
        except Exception:
            pass
        finally:
            try:
                pass
            except Exception:
                self.log.exception("Exception in post_request hook")






