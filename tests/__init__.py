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
       
    print "\n\nRUNNING TESTS FOR: collide.py:"
    collide.runSuite(VB)
    
    print "\n\nRUNNING TESTS FOR: server.py:"
    server.runSuite(VB)
    
    print "\n\nRUNNING TESTS FOR: config.py:"
    config.runSuite(VB)
        
    print "\n\nRUNNING TESTS FOR: game.py:"
    game.runSuite(VB)
    
    print "\nEND TESTS"
    
# vim: et sw=4 sts=4
