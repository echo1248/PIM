# -*- coding: utf-8 -*-
# File   @ util.py
# Create @ 2019/2/26 10:04
# Author @ 819070918@qq.com

import os
import re
import sys
import fcntl
import traceback
from server.workers import SUPPORTED_WORKERS
from importlib import import_module


def close_on_exec(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    flags |= fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def set_non_blocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


def parse_address(netloc, default_port=8000):
    if re.match(r'unix:(//)?', netloc):
        return re.split(r'unix:(//)?', netloc)[-1]

    if netloc.startswith("tcp://"):
        netloc = netloc.split("tcp://")[1]

    # get host
    if '[' in netloc and ']' in netloc:
        host = netloc.split(']')[0][1:].lower()
    elif ':' in netloc:
        host = netloc.split(':')[0].lower()
    elif netloc == "":
        host = "0.0.0.0"
    else:
        host = netloc.lower()

    netloc = netloc.split(']')[-1]
    if ":" in netloc:
        port = netloc.split(':', 1)[1]
        if not port.isdigit():
            raise RuntimeError("%r is not a valid port number." % port)
        port = int(port)
    else:
        port = default_port
    return (host, port)


def load_class(uri):

    components = SUPPORTED_WORKERS[uri].split(".")

    klass = components.pop(-1)
    try:
        mod = import_module('.'.join(components))
    except:
        exc = traceback.format_exc()
        msg = "class uri %r invalid or not found: \n\n[%s]"
        raise RuntimeError(msg % (uri, exc))
    return getattr(mod, klass)


def import_app(module):
    parts = module.split(":", 1)
    if len(parts) == 1:
        module, obj = module, "application"
    else:
        module, obj = parts[0], parts[1]

    try:
        __import__(module)
    except ImportError:
        if module.endswith(".py") and os.path.exists(module):
            msg = "Failed to find application, did you mean '%s:%s'?"
            raise ImportError(msg % (module.rsplit(".", 1)[0], obj))
        else:
            raise

    mod = sys.modules[module]

    try:
        app = eval(obj, vars(mod))
    except NameError:
        raise AppImportError("Failed to find application object %r in %r" % (obj, module))

    if app is None:
        raise AppImportError("Failed to find application object: %r" % obj)

    if not callable(app):
        raise AppImportError("Application object must be callable.")
    return app
