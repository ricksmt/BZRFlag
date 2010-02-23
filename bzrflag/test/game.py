#!/usr/bin/env python
import magictest
from .. import game

g = None
def getGame():
    global g
    if g is not None:
        g.remake()
        return g
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

class GameTest(magictest.MagicTest):
    def setUp(self):
        self.game = getGame()

    def tearDown(self):
        self.game = None

class MapTest(GameTest):
    def testTanks(self):
        self.assertEquals(len(list(self.game.map.tanks())), 40)
    def testShots(self):
        self.assertEquals(len(list(self.game.map.shots())), 0)

class TeamTest(GameTest):
    def setUp(self):
        GameTest.setUp(self)
        self.team = self.game.map.teams['green']
    def testSetup(self):
        self.assertNotEqual(self.team._obstacles,[])


def runSuite():
    result = Initial.runSuite()
    if result.wasSuccessful():
        MapTest.runSuite()
        TeamTest.runSuite()



# vim: et sw=4 sts=4
