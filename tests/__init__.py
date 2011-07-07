#!/usr/bin/env python
import unittest

import config
import collide
import server
import game
from bzrflag import constants # to make sure we can

VB = 2

def run():
    print "\nSTART TESTS"
       
    print "\nRunning tests for collide.py:"
    collide.runSuite(VB)
    
    print "\nRunning tests for config.py:"
    config.runSuite(VB)
    
    print "\nRunning tests for server.py:"
    server.runSuite(VB)
        
    print "\nRunning tests for game.py:"
    game.runSuite(VB)
    
    print "\nEND TESTS"
    
# vim: et sw=4 sts=4
