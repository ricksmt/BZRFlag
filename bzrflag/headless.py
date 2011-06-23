'''headless.py

defines a Display class and an Input class
for a headless station

'''

import asyncore
import logging

import server
import constants
import config
import graphics

logger = logging.getLogger('headless.py')

# A higher loop timeout decreases CPU usage but also decreases the frame rate.
LOOP_TIMEOUT = 0.01


class Display(graphics.Display):

    def update(self):
        pass
        
    def setup(self):
        pass


class Input:
    '''The server input class'''
    
    def __init__(self, game):
        self.game = game
        self.servers = {}
        for color,team in self.game.map.teams.items():
            self.servers[color] = server.Server(
                    ('0.0.0.0', config.config[color+'_port']),team)
            #logger.debug("Listening op port %s for team %s"
            # %(self.servers[color].get_port(), color))
            print 'port for %s: %s' % (color, self.servers[color].get_port())
        print

    def update(self):
        asyncore.loop(LOOP_TIMEOUT, count = 1)
