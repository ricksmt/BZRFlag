#!/usr/bin/env python
import os

import magictest
from bzrflag import server, config

class ServerTest(magictest.MagicTest):
    
    def setUp(self):
        self.config_file = config.Config()
        
    def tearDown(self):
        self.config_file = None

    def testInitialization(self):
        team = None
        s = server.Server(('0.0.0.0', 50100),team, self.config_file)
        self.assertEquals(s.get_port(), 50100)
        
        
def runSuite(vb=2):
    return ServerTest.runSuite(vb)

# vim: et sw=4 sts=4
