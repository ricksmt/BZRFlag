#!/usr/bin/env python
import os

import magictest
from bzrflag import server, config

config_file = None

class ServerTest(magictest.MagicTest):
    
    def setUp(self):
        global config_file
        config_file = config.Config()

    def test_build(self):
        team = None
        s = server.Server(('0.0.0.0', 50100),team, config_file)
        self.assertEquals(s.get_port(), 50100)
        
        
def runSuite(vb=2):
    return ServerTest.runSuite(vb)


