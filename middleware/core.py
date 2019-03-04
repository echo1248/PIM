# -*- coding: utf-8 -*-
# File   @ core.py
# Create @ 2019/3/1 15:03
# Author @ 819070918@qq.com


from middleware.msg import process


def application(data, sour_addr, callback):
    process(data, sour_addr, callback)

