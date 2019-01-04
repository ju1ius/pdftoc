#! /usr/bin/env python3
# coding=utf8
import sys

from pdftoc.app import Application


if __name__ == "__main__":

    app = Application()
    app.run(sys.argv)

    sys.exit(0)
