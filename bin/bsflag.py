#!/usr/bin/env python

import os
import sys

basedir, bin = os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))
sys.path.append(basedir)

import bsflag
bsflag.run()

# vim: et sw=4 sts=4
