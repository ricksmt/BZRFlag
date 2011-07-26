#!/usr/bin/env python
import os

import unittest
from bzrflag import config


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.world = ""+os.path.join(os.path.dirname(__file__), "test.bzw")
        self.port = "50100"
        self.config_file = config.Config(["--world="+self.world,
                                          "--red-port="+self.port])

    def tearDown(self):
        self.config_file = None

    def testArgError(self):
        args = '--world=test_bad.bzw --red-port=50189'.split()
        self.assertRaises(config.ArgumentError, config.Config,args)

    def testOptions(self):
        self.assertEquals(self.config_file['world'], self.world)
        self.assertEquals(self.config_file['red_port'], int(self.port))

# vim: et sw=4 sts=4
