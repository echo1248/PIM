# -*- coding: utf-8 -*-
# File   @ cache.py
# Create @ 2019/3/4 17:53
# Author @ 819070918@qq.com


class Cache(object):

    def __init__(self):
        self.memo = {}

    def __getitem__(self, item):
        return self.memo[item]

    def __setitem__(self, key, value):
        self.memo[key] = value

    def __delitem__(self, key):
        if key in self.memo:
            del self.memo[key]
