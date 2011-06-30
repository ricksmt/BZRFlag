"""headless.py

Defines a Display class and an Input class
for a headless station.

"""

import asyncore
import logging

import server
import constants
import config
import graphics 
from constants import LOOP_TIMEOUT  

logger = logging.getLogger('headless.py')


class Display(graphics.Display):

    def update(self):
        pass
        
    def setup(self):
        pass


class Input:
    """The server input class."""
    
    def __init__(self, game):
        self.game = game
        self.servers = {}
        for color,team in self.game.map.teams.items():
            self.servers[color] = server.Server(
                    ('0.0.0.0', config.config[color+'_port']),team)
            print 'port for %s: %s' % (color, self.servers[color].get_port())
        print

    def update(self):
        asyncore.loop(LOOP_TIMEOUT, count = 1)
