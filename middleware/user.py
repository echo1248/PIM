# -*- coding: utf-8 -*-
# File   @ user.py
# Create @ 2019/2/26 10:27
# Author @ 819070918@qq.com

import time

from middleware.cache import Cache


class User(object):
    users = Cache()

    @classmethod
    def search(cls, u_id):
        if u_id not in cls.users:
            return None

        ip, port, timestamp = cls.users[u_id].split("$")
        if time.time() > timestamp + 60:
            return None

        return ip, port

    @classmethod
    def online(cls, u_id, address, timestamp):
        cls.users[u_id] = "{}${}${}".format(address[0], address[1], timestamp)

    @classmethod
    def offline(cls, u_id):
        if u_id in cls.users:
            del cls.users[u_id]




