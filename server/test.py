# -*- coding: utf-8 -*-
# File   @ test.py
# Create @ 2019/3/1 14:23
# Author @ 819070918@qq.com

import argparse


def main():
    kwargs = {
        "usage": "%(prog)s [OPTIONS] [APP_MODULE]",
        "prog": "pim"
    }
    parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument("-v", "--version",
                        action="version", default=argparse.SUPPRESS,
                        version="%(prog)s (version " + "1.0.0" + ")\n",
                        help="show program's version number and exit")
    parser.add_argument(*("-b", "--bind"), **{}, help=argparse.SUPPRESS)
    parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

    args = parser.parse_args()
    print(args.args)


if __name__ == '__main__':
    main()
