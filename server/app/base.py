# -*- coding: utf-8 -*-
# File   @ base.py
# Create @ 2019/2/26 10:24
# Author @ 819070918@qq.com

import sys
from server.arbiter import Arbiter
from server.config import Config


class BaseApplication(object):

    def __init__(self, usage=None, prog=None):

        self.usage = usage
        self.prog = prog
        self.cfg = None
        self.callable = None
        self.logger = None
        self.do_load_config()

    def do_load_config(self):
        """
        Loads the configuration
        """
        try:
            self.load_default_config()
            self.load_config()

        except Exception as e:
            print("\nError: %s" % str(e), file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)

    def load_default_config(self):
        self.cfg = Config(self.usage, prog=self.prog)

    def init(self, parser, opts, args):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def load_config(self):
        raise NotImplementedError

    def reload(self):
        self.do_load_config()

    def middleware(self):
        if self.callable is None:
            self.callable = self.load()
        return self.callable

    def run(self):
        try:
            Arbiter(self).run()
        except RuntimeError as e:
            print("\nError: %s\n" % e, file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)


class Application(BaseApplication):

    def load_config(self):
        parser = self.cfg.parser()
        args = parser.parse_args()

        # optional settings from apps
        cfg = self.init(parser, args, args.args)

    def run(self):
        super(Application, self).run()
