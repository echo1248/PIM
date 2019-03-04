# -*- coding: utf-8 -*-
# File   @ msg.py
# Create @ 2019/2/26 10:06
# Author @ 819070918@qq.com

import json
import uuid
import time

from middleware.cache import Cache
from middleware.user import User


IM = 1
ACK = 2
HEAT_BEAT = 3
ONLINE = 4
OFFLINE = 5
IM_GROUP = 6


def process(data, sour_addr, callback):
    funcs = {
        IM: func_im,
        ACK: func_ack,
        HEAT_BEAT: func_heat_beat,
        ONLINE: func_online,
        OFFLINE: func_offline,
        IM_GROUP: func_im_group,
    }
    msg = Msg(data)

    return funcs[msg.m_type](msg, sour_addr, callback)


def func_im(msg, sour_addr, callback):
    User.online(msg.sour_id, sour_addr, msg.timestamp)

    ack_msg = Msg.create_ack(msg.m_id, msg.sour_id)
    callback(ack_msg, sour_addr)

    im_msg = Msg.create_im(msg.m_body, msg.sour_id, msg.dest_id)
    dest_addr = User.search(msg.dest_id)
    if dest_addr:
        callback(im_msg, dest_addr)


def func_ack(msg, sour_addr, callback):
    User.online(msg.sour_id, sour_addr, msg.timestamp)
    Msg.ack(msg.m_id)


def func_heat_beat(msg, sour_addr, callback):
    User.online(msg.sour_id, sour_addr, msg.timestamp)


def func_online(msg, sour_addr, callback):
    User.online(msg.sour_id, sour_addr, msg.timestamp)


def func_offline(msg, sour_addr, callback):
    User.offline(msg.sour_id)


def func_im_group(msg, sour_addr, callback):
    pass


class Msg(object):

    msgs = Cache()

    def __init__(self, data):
        msg = json.loads(data)
        self._m_id = msg["id"]
        self._m_body = msg["body"]
        self._m_type, self._sour_id, self._dest_id, self._timestamp = msg["head"].split("$")
        self.msgs[msg["id"]] = {"body": msg["body"], "head": msg["head"]}

    def _get_m_id(self):
        return self._m_id

    def _get_m_body(self):
        return self._m_body

    def _get_m_type(self):
        return self._m_type

    def _get_sour_id(self):
        return self._sour_id

    def _get_dest_id(self):
        return self._dest_id

    def _get_timestamp(self):
        return self._timestamp

    m_id = property(_get_m_id)
    m_body = property(_get_m_body)
    m_type = property(_get_m_type)
    sour_id = property(_get_sour_id)
    dest_id = property(_get_dest_id)
    timestamp = property(_get_timestamp)

    @classmethod
    def ack(cls, m_id):
        if m_id in cls.msgs:
            del cls.msgs[m_id]

    @staticmethod
    def create_msg(m_type=None, m_body=None, sour_id=None, dest_id=None):
        msg = {
            "id": str(uuid.uuid1()),
            "head": "{}${}${}${}".format(m_type, sour_id, dest_id, int(time.time())),
            "body": m_body
        }
        return bytes(json.dumps(msg), encoding="utf8")

    @classmethod
    def create_im(cls, m_body, sour_id, dest_id):
        return cls.create_msg(m_type=IM, m_body=m_body, sour_id=sour_id, dest_id=dest_id)

    @classmethod
    def create_ack(cls, m_id, sour_id):
        return cls.create_msg(m_type=ACK, m_body=m_id, sour_id=sour_id)

    @classmethod
    def create_heat_beat(cls, sour_id):
        return cls.create_msg(m_type=HEAT_BEAT, sour_id=sour_id)

    @classmethod
    def create_online(cls, sour_id):
        return cls.create_msg(m_type=ONLINE, sour_id=sour_id)

    @classmethod
    def create_offline(cls, sour_id):
        return cls.create_msg(m_type=OFFLINE, sour_id=sour_id)



