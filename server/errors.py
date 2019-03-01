# -*- coding: utf-8 -*-
# File   @ errors.py
# Create @ 2019/3/1 15:28
# Author @ 819070918@qq.com


class ConfigError(Exception):
    """ Exception raised on config error """


class AppImportError(Exception):
    """ Exception raised when loading an application """
