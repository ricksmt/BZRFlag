#!/usr/bin/env python
import os

import magictest
from bzrflag import server, config

class ServerTest(magictest.MagicTest):
    
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
              
           
def runSuite(vb=2):
    return ServerTest.runSuite(vb)

# vim: et sw=4 sts=4
