#!/usr/bin/env python
import unittest

import config
import collide
from .. import constants # to make sure we can
import game

def run():
    config.Test.runSuite()
    collide.runSuite()
    game.runSuite()
# vim: et sw=4 sts=4
