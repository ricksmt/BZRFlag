#!/usr/bin/env python
import magictest
from bzrflag import config

g = None


def getGame():
    global g
    if g is not None:
        g.remake()
        return g
    config.init()
    from bzrflag import game # Cannot import before config.init() is called!
    g = game.Game()
    g.display.setup()
    g.input.update()
    g.update()
    g.update_sprites()
    g.display.update()
    return g


class Initial(magictest.MagicTest):

    def testCreate(self):
        g = getGame()
        self.assertIsNot(g,None)
 

class GameTest(magictest.MagicTest):

    def setUp(self):
        self.game = getGame()

    def tearDown(self):
        self.game = None

    def testTanks(self):
        self.assertEquals(len(list(self.game.map.tanks())), 40)
        
    def testShots(self):
        self.assertEquals(len(list(self.game.map.shots())), 0)
        
    def testTeam(self):
        self.team = self.game.map.teams['green']
        self.assertNotEqual(self.team._obstacles,[])


def runSuite(vb=2):
    result = Initial.runSuite(vb)
    if result.wasSuccessful():
        GameTest.runSuite(vb)


# vim: et sw=4 sts=4
