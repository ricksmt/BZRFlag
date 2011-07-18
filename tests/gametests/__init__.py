#!/usr/bin/env python
import unittest
import datetime

import testcommands

VB = 2

def run():
    print datetime.datetime.now()
    print "\nSTART GAME TESTS"
       
    print "\n\nRUNNING COMMANDS TESTS:"
    testcommands.run(VB)

    print "\nEND GAME TESTS"
    
# vim: et sw=4 sts=4
