#!/usr/bin/env python
import os

import magictest
from bzrflag import game, config


class GameTest(magictest.MagicTest):

    def setUp(self):  
        world = "--world="+os.path.join(os.path.dirname(__file__), "test.bzw")
        config_file = config.Config([world])
        self.game = game.Game(config_file, "test")
        self.game.input.update()
        self.game.update()
        
        ## Set up connection to server to test commands

    def tearDown(self):
        self.game = None
        
    def testInitialization(self):
        self.team = self.game.map.teams['green']
        self.assertNotEqual(self.team._obstacles,[])
        self.assertEquals(len(list(self.game.map.tanks())), 40)
        self.assertEquals(len(list(self.game.map.shots())), 0)
        
    def testTaunt(self):
        print "pass"
        
    def testHelp(self):
        print "pass"
    
    def testShoot(self):
        print "pass"
        
    def testSpeed(self):
        print "pass"
        
    def testAngvel(self):
       print "pass"
    
    def testTeams(self):
        print "pass"
        
    def testObstacles(self):
        print "pass"
    
    def testOccgrid(self):
        print "pass"
        
    def testBases(self):
        print "pass"
    
    def testFlags(self):
        print "pass"
        
    def testShots(self):
        print "pass"
    
    def testMytanks(self):
        print "pass"
        
    def testOthertanks(self):
        print "pass"
    
    def testConstants(self):
        print "pass"
        
    def testScores(self):
        print "pass"
        
    def testTimer(self):
        print "pass"
        
    def testQuit(self):
        print "pass"

def runSuite(vb=2):
    GameTest.runSuite(vb)


# vim: et sw=4 sts=4
