# -*- coding: utf-8 -*-
# File   @ sock.py
# Create @ 2019/2/26 11:02
# Author @ 819070918@qq.com

import sys
import time
import errno
import socket


class BaseSocket(object):

    def __init__(self, address, conf, log):
        self.log = log
        self.conf = conf

        self.cfg_addr = address
        sock = socket.socket(self.FAMILY, socket.SOCK_DGRAM)
        bound = False

        self.sock = self.set_options(sock, bound=bound)

    def __str__(self):
        return "<socket %d>" % self.sock.fileno()

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def set_options(self, sock, bound=False):

        if not bound:
            self.bind(sock)
        sock.setblocking(0)

        return sock

    def bind(self, sock):
        sock.bind(self.cfg_addr)

    def close(self):
        if self.sock is None:
            return

        try:
            self.sock.close()
        except socket.error as e:
            print("Error while closing socket %s", str(e))

        self.sock = None


class UDPSocket(BaseSocket):
    FAMILY = socket.AF_INET

    def set_options(self, sock, bound=False):
        return super(UDPSocket, self).set_options(sock, bound=bound)


def _sock_type(addr):
    sock_type = UDPSocket
    return sock_type


def create_sockets(conf, log):
    """
    Create a new socket for the configured addresses or file descriptors.

    """
    listeners = []

    # get it only once
    laddr = conf.address

    for addr in laddr:
        sock_type = _sock_type(addr)
        sock = None
        for i in range(5):
            try:
                sock = sock_type(addr, conf, log)
            except socket.error as e:
                if e.args[0] == errno.EADDRINUSE:
                    print("Connection in use: %s", str(addr))
                if e.args[0] == errno.EADDRNOTAVAIL:
                    print("Invalid address: %s", str(addr))
                if i < 5:
                    msg = "connection to {addr} failed: {error}"
                    print(msg.format(addr=str(addr), error=str(e)))
                    print("Retrying in 1 second.")
                    time.sleep(1)
            else:
                break

        if sock is None:
            print("Can't connect to %s", str(addr))
            sys.exit(1)

        listeners.append(sock)

    return listeners


def close_sockets(listeners):
    for sock in listeners:
        sock.close()





