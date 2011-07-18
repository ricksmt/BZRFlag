#!/usr/bin/env python
import unittest
import datetime

import collide
import config
import server
import game

VB = 2

def run():
    print datetime.datetime.now()
    print "\nSTART CODE TESTS"
       
    print "\n\nRUNNING TESTS FOR: collide.py:"
    #collide.runSuite(VB)
    
    print "\n\nRUNNING TESTS FOR: config.py:"
    config.runSuite(VB)
    
    print "\n\nRUNNING TESTS FOR: server.py:"
    server.runSuite(VB)
        
    print "\n\nRUNNING TESTS FOR: game.py:"
    game.runSuite(VB)

    print "\nEND CODE TESTS"
    
# vim: et sw=4 sts=4
