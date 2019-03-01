# -*- coding: utf-8 -*-
# File   @ selectors.py
# Create @ 2019/2/26 11:27
# Author @ 819070918@qq.com


from abc import ABCMeta, abstractmethod
from collections import namedtuple, Mapping
import math
import select
import sys

# generic events, that must be mapped to implementation-specific ones
EVENT_READ = (1 << 0)
EVENT_WRITE = (1 << 1)


def _fileobj_to_fd(fileobj):

    if isinstance(fileobj, int):
        fd = fileobj
    else:
        try:
            fd = int(fileobj.fileno())
        except (AttributeError, TypeError, ValueError):
            raise ValueError("Invalid file object: "
                             "{0!r}".format(fileobj))
    if fd < 0:
        raise ValueError("Invalid file descriptor: {0}".format(fd))
    return fd


SelectorKey = namedtuple('SelectorKey', ['fileobj', 'fd', 'events', 'data'])


class _SelectorMapping(Mapping):

    def __init__(self, selector):
        self._selector = selector

    def __len__(self):
        return len(self._selector)

    def __getitem__(self, fileobj):
        pass

    def __iter__(self):
        pass


class BaseSelector(metaclass=ABCMeta):

    @abstractmethod
    def register(self, fileobj, events, data=None):
        raise NotImplementedError

    @abstractmethod
    def unregister(self, fileobj):
        raise NotImplementedError

    @abstractmethod
    def modify(self, fileobj, events, data=None):
        self.unregister(fileobj)
        return self.register(fileobj, events, data)

    @abstractmethod
    def select(self, timeout):
        raise NotImplementedError

    @abstractmethod
    def get_map(self):
        raise NotImplementedError

    def get_key(self, fileobj):
        mapping = self.get_map()
        try:
            return mapping[fileobj]
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _BaseSelectorImpl(BaseSelector):

    def __init__(self):
        self._fd_to_key = {}
        self._map = _SelectorMapping(self)

    def _fileobj_lookup(self, fileobj):
        try:
            return _fileobj_to_fd(fileobj)
        except ValueError:
            # Do an exhaustive search.
            for key in self._fd_to_key.values():
                if key.fileobj is fileobj:
                    return key.fd
            # Raise ValueError after all.
            raise

    def register(self, fileobj, events, data=None):
        if (not events) or (events & ~(EVENT_READ | EVENT_WRITE)):
            raise ValueError("Invalid events: {0!r}".format(events))

        key = SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)

        if key.fd in self._fd_to_key:
            raise KeyError("{0!r} (FD {1}) is already registered"
                           .format(fileobj, key.fd))

        self._fd_to_key[key.fd] = key
        return key

    def unregister(self, fileobj):

        try:
            key = self._fd_to_key.pop(self._fileobj_lookup(fileobj))
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))
        return key

    def modify(self, fileobj, events, data=None):

        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            raise KeyError("{0!r} is not registered".format(fileobj))

        if events != key.events:
            self.unregister(fileobj)
            self.register(fileobj, events, data)
        elif data != key.data:
            key = key._replace(data=data)
            self._fd_to_key[key.fd] = key
        return key

    def close(self):
        self._fd_to_key.clear()

    def get_map(self):
        return self._map

    def _key_from_fd(self, fd):
        try:
            return self._fd_to_key[fd]
        except KeyError:
            return None













