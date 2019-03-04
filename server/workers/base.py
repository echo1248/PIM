# -*- coding: utf-8 -*-
# File   @ base.py
# Create @ 2019/2/26 10:19
# Author @ 819070918@qq.com

import os
import sys
import time
import signal
from server import util


class Worker(object):

    SIGNALS = [getattr(signal, "SIG%s" % x)
               for x in "ABRT HUP QUIT INT TERM USR1 USR2 WINCH CHLD".split()]

    PIPE = []

    def __init__(self, age, ppid, sockets, app, cfg, log):
        self.age = age
        self.pid = "[booting]"
        self.ppid = ppid
        self.sockets = sockets
        self.app = app
        self.cfg = cfg
        self.booted = False

        self.alive = True
        self.log = log

    def __str__(self):
        return "<Worker %s>" % self.pid

    def run(self):
        """\
        This is the mainloop of a worker process. You should override
        this method in a subclass to provide the intended behaviour
        for your particular evil schemes.
        """
        raise NotImplementedError()

    def init_process(self):

        self.PIPE = os.pipe()
        self.wait_fds = self.sockets + [self.PIPE[0]]
        for p in self.PIPE:
            util.set_non_blocking(p)
            util.close_on_exec(p)
        self.middleware = self.app.middleware()
        # Enter main run loop
        self.booted = True
        self.run()

    def init_signals(self):
        # reset signaling
        for s in self.SIGNALS:
            signal.signal(s, signal.SIG_DFL)
        # init new signaling
        signal.signal(signal.SIGQUIT, self.handle_quit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_quit)
        signal.signal(signal.SIGWINCH, self.handle_winch)
        signal.signal(signal.SIGUSR1, self.handle_usr1)
        signal.signal(signal.SIGABRT, self.handle_abort)

        # Don't let SIGTERM and SIGUSR1 disturb active requests
        # by interrupting system calls
        if hasattr(signal, 'siginterrupt'):  # python >= 2.6
            signal.siginterrupt(signal.SIGTERM, False)
            signal.siginterrupt(signal.SIGUSR1, False)

    def handle_usr1(self, sig, frame):
        self.log.reopen_files()

    def handle_exit(self, sig, frame):
        self.alive = False

    def handle_quit(self, sig, frame):
        self.alive = False
        # worker_int callback
        self.cfg.worker_int(self)
        time.sleep(0.1)
        sys.exit(0)

    def handle_abort(self, sig, frame):
        self.alive = False
        self.cfg.worker_abort(self)
        sys.exit(1)

    def handle_winch(self, sig, fname):
        # Ignore SIGWINCH in worker. Fixes a crash on OpenBSD.
        self.log.debug("worker: SIGWINCH ignored.")


