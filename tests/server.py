#!/usr/bin/env python
import os

import unittest
from bzrflag import server, config

class ServerTest(unittest.TestCase):

    def setUp(self):
        self.config = config.Config()
        team = None
        map = None
        self.srv = server.Server(('0.0.0.0', 0), team, map, self.config)
        self.port = self.srv.get_port()

    def tearDown(self):
        self.config_file = None
        self.srv = None
        self.port = None

    def testInitialization(self):
        self.assertEquals(self.srv.in_use, False)

# vim: et sw=4 sts=4
