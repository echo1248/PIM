# -*- coding: utf-8 -*-
# File   @ sync.py
# Create @ 2019/2/26 10:19
# Author @ 819070918@qq.com


import os
import errno
import select
import server.workers.base as base


class StopWaiting(Exception):
    """ exception raised to stop waiting for a connnection """


class SyncWorker(base.Worker):

    BUF_SIZE = 1024

    def sendto(self, data, addr):
        listener = self.sockets[0]
        if isinstance(data, str):
            data = bytes(data, encoding="utf8")
        listener.sendto(data, addr)

    def recvfrom(self, listener):
        data, addr = listener.recvfrom(self.BUF_SIZE)
        self.handle(data, addr)

    def wait(self, timeout):
        try:
            ret = select.select(self.wait_fds, [], [], timeout)
            if ret[0]:
                if self.PIPE[0] in ret[0]:
                    os.read(self.PIPE[0], 1)
                return ret[0]

        except select.error as e:
            if e.args[0] == errno.EINTR:
                return self.sockets
            if e.args[0] == errno.EBADF:
                raise StopWaiting
            raise

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

            try:
                self.wait(1)
            except StopWaiting:
                return

    def handle(self, data, client):
        try:
            respiter = self.middleware(data, client, self.sendto)
            self.sendto(respiter.data, respiter.addr)
        except Exception:
            pass

