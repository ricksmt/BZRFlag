#!/usr/bin/env python
import unittest

import config
import collide
import game
from bzrflag import constants # to make sure we can


def run():
    print "\nRunning tests for config.py:"
    config.runSuite(1)
    print "\nRunning tests for collide.py:"
    collide.runSuite(1)
    print "\nRunning tests for game.py:"
    game.runSuite(1)
    
# vim: et sw=4 sts=4
