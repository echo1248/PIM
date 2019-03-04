# -*- coding: utf-8 -*-
# File   @ arbiter.py
# Create @ 2019/2/26 10:17
# Author @ 819070918@qq.com

import os
import sys
import time
import random
import select
import signal
import errno
import traceback
from server import sock
from server import SERVER_SOFTWARE
from server import util
from server.errors import AppImportError


class Arbiter(object):
    WORKER_BOOT_ERROR = 3
    APP_LOAD_ERROR = 4
    LISTENERS = []
    WORKERS = {}

    PIPE = []
    SIG_QUEUE = []
    SIGNALS = [getattr(signal, "SIG%s" % x)
               for x in "HUP QUIT INT TERM TTIN TTOU USR1 USR2 WINCH".split()]
    SIG_NAMES = dict(
        (getattr(signal, name), name[3:].lower()) for name in dir(signal)
        if name[:3] == "SIG" and name[3] != "_"
    )

    def __init__(self, app):
        os.environ["SERVER_SOFTWARE"] = SERVER_SOFTWARE

        self.pidfile = None
        self._num_workers = None
        self.worker_age = 0

        self.setup(app)

    def _get_num_workers(self):
        return self._num_workers

    def _set_num_workers(self, value):
        self._num_workers = value

    num_workers = property(_get_num_workers, _set_num_workers)

    def setup(self, app):
        self.app = app
        self.cfg = app.cfg

        self.worker_class = self.cfg.worker_class
        self.address = self.cfg.address
        self.num_workers = self.cfg.workers

    def start(self):
        """
          Initialize the arbiter. Start listening and set pidfile if needed.
        """
        self.pid = os.getpid()

        self.init_signals()

        self.LISTENERS = sock.create_sockets(self.cfg, None)

    def init_signals(self):
        """\
        Initialize master signal handling. Most of the signals
        are queued. Child signals only wake up the master.
        """
        # close old PIPE
        for p in self.PIPE:
            os.close(p)

        # initialize the pipe
        self.PIPE = pair = os.pipe()
        for p in pair:
            util.set_non_blocking(p)
            util.close_on_exec(p)

        # initialize all signals
        for s in self.SIGNALS:
            signal.signal(s, self.signal)

    def signal(self, sig, frame):
        if len(self.SIG_QUEUE) < 5:
            self.SIG_QUEUE.append(sig)
            self.wakeup()

    def run(self):
        """
          Main master loop.
        """
        self.start()
        try:
            self.manage_workers()

            while True:
                sig = self.SIG_QUEUE.pop(0) if self.SIG_QUEUE else None
                if sig is None:
                    self.sleep()
                    continue

                if sig not in self.SIG_NAMES:
                    continue

                signame = self.SIG_NAMES.get(sig)
                handler = getattr(self, "handle_%s" % signame, None)
                if not handler:
                    continue
                handler()
                self.wakeup()
        except StopIteration:
            self.halt()
        except KeyboardInterrupt:
            self.halt()
        except SystemExit:
            raise
        except Exception as EX:
            print("arbiter: error={}, {}".format(EX, traceback.format_exc()))
            if self.pidfile is not None:
                self.pidfile.unlink()
            sys.exit(-1)

    def sleep(self):
        """\
        Sleep until PIPE is readable or we timeout.
        A readable PIPE means a signal occurred.
        """
        try:
            ready = select.select([self.PIPE[0]], [], [], 1.0)
            if not ready[0]:
                return
            while os.read(self.PIPE[0], 1):
                pass
        except (select.error, OSError) as e:
            error_number = getattr(e, 'errno', e.args[0])
            if error_number not in [errno.EAGAIN, errno.EINTR]:
                raise
        except KeyboardInterrupt:
            sys.exit()

    def wakeup(self):
        """\
        Wake up the arbiter by writing to the PIPE
        """
        try:
            os.write(self.PIPE[1], b'.')
        except IOError as e:
            if e.errno not in [errno.EAGAIN, errno.EINTR]:
                raise

    def halt(self, exit_status=0):
        """ halt arbiter """
        self.stop()
        if self.pidfile is not None:
            self.pidfile.unlink()
        sys.exit(exit_status)

    def stop(self, graceful=True):
        """\
        Stop workers

        :attr graceful: boolean, If True (the default) workers will be
        killed gracefully  (ie. trying to wait for the current connection)
        """

        sock.close_sockets(self.LISTENERS)

        self.LISTENERS = []
        sig = signal.SIGTERM
        if not graceful:
            sig = signal.SIGQUIT
        # instruct the workers to exit
        self.kill_workers(sig)
        # wait until the graceful timeout
        time.sleep(0.1)

        self.kill_workers(signal.SIGKILL)

    def kill_workers(self, sig):
        """\
        Kill all workers with the signal `sig`
        :attr sig: `signal.SIG*` value
        """
        worker_pids = list(self.WORKERS.keys())
        for pid in worker_pids:
            self.kill_worker(pid, sig)

    def kill_worker(self, pid, sig):
        """\
        Kill a worker

        :attr pid: int, worker pid
        :attr sig: `signal.SIG*` value
         """
        try:
            os.kill(pid, sig)
        except OSError as e:
            raise

    def murder_workers(self):
        """\
        Kill unused/idle workers
        """
        workers = list(self.WORKERS.items())
        for (pid, worker) in workers:

            if not worker.aborted:
                worker.aborted = True
                self.kill_worker(pid, signal.SIGABRT)
            else:
                self.kill_worker(pid, signal.SIGKILL)

    def manage_workers(self):
        """\
        Maintain the number of workers by spawning or killing
        as required.
        """
        if len(self.WORKERS) < self.num_workers:
            self.spawn_workers()

        workers = self.WORKERS.items()
        workers = sorted(workers, key=lambda w: w[1].age)
        while len(workers) > self.num_workers:
            (pid, _) = workers.pop(0)
            self.kill_worker(pid, signal.SIGTERM)

    def spawn_worker(self):
        self.worker_age += 1
        worker = self.worker_class(self.worker_age, self.pid, self.LISTENERS, self.app, self.cfg, None)

        pid = os.fork()
        if pid != 0:
            worker.pid = pid
            self.WORKERS[pid] = worker
            return pid
        # Process Child
        worker.pid = os.getpid()
        try:
            worker.init_process()
            sys.exit(0)
        except SystemExit:
            raise
        except AppImportError as e:
            sys.stderr.flush()
            sys.exit(self.APP_LOAD_ERROR)
        except:
            if not worker.booted:
                sys.exit(self.WORKER_BOOT_ERROR)
            sys.exit(-1)

    def spawn_workers(self):
        """\
        Spawn new workers as needed.

        This is where a worker process leaves the main loop
        of the master process.
        """

        for _ in range(self.num_workers - len(self.WORKERS)):
            self.spawn_worker()
            time.sleep(0.1 * random.random())

    def handle_int(self):
        "SIGINT handling"
        self.stop(False)
        raise StopIteration
