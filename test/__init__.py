#!/usr/bin/env python
import unittest

import config
import collide
import game
from .. import constants # to make sure we can


def run():
    config.Test.runSuite()
    collide.runSuite()
    game.runSuite()
    
# vim: et sw=4 sts=4
