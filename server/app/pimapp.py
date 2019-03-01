# -*- coding: utf-8 -*-
# File   @ app.py
# Create @ 2019/2/26 10:18
# Author @ 819070918@qq.com

from server import util
from server.app.base import Application


class PimApplication(Application):

    def init(self, parser, opts, args):
        self.middleware_url = args[0]

    def load_middleware(self):
        return util.import_app(self.middleware_url)

    def load(self):
        return self.load_middleware()


def run():
    PimApplication("%(prog)s [OPTIONS] [APP_MODULE]").run()


if __name__ == '__main__':
    run()
