#!/usr/bin/env python
import unittest
import doctest

from bzrflag import collide

def toSuite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(collide))
    return suite


def runSuite(vb=2):
    return unittest.TextTestRunner(verbosity=vb).run(toSuite())


# vim: et sw=4 sts=4
