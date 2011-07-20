#!/usr/bin/env python
import os

import unittest
from bzrflag import server, config

class ServerTest(unittest.TestCase):
    
    def setUp(self):
        self.config_file = config.Config()
        self.team = None
        self.svr = server.Server(('0.0.0.0', 0), self.team, self.config_file)
        self.port = self.svr.get_port() 
        
    def tearDown(self):
        self.config_file = None
        self.svr = None
        self.port = None

    def testInitialization(self):
        self.assertEquals(self.svr.in_use, False)

# vim: et sw=4 sts=4
