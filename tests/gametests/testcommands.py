#!/usr/bin/env python
from tests import magictest

class CommandsTest(magictest.MagicTest):

    def setUp(self):  
        pass
        
    def tearDown(self):
        pass

    def test_commands(self):
       print "FAIL"
            

def run(vb=2):
    return CommandsTest.runSuite(vb)



# vim: et sw=4 sts=4
