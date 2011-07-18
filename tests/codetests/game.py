#!/usr/bin/env python
import os

from tests import magictest
from bzrflag import game, config


class GameTest(magictest.MagicTest):

    def setUp(self):  
        world = "--world="+os.path.join(os.path.dirname(__file__), "test.bzw")
        self.config = config.Config(['--test', world])
        self.game = game.Game(self.config)
        self.game.input.update()
        self.game.update()
        self.team = "red"
        self.port = self.game.input.servers[self.team].get_port()
        
    def tearDown(self):
        self.game = None

    def testInitialization(self):
        self.team = self.game.map.teams['green']
        self.assertNotEqual(self.team._obstacles,[])
        self.assertEquals(len(list(self.game.map.tanks())), 40)
        self.assertEquals(len(list(self.game.map.shots())), 0)
            

def runSuite(vb=2):
    return GameTest.runSuite(vb)


# vim: et sw=4 sts=4
