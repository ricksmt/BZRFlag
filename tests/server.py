#!/usr/bin/env python
import os

import magictest
from bzrflag import server

class ServerTest(magictest.MagicTest):

    def test_build(self):
        team = None
        s = server.Server(('0.0.0.0', 50100),team)
        self.assertEquals(s.get_port(), 50100)
        
        
def runSuite(vb=2):
    return ServerTest.runSuite(vb)


