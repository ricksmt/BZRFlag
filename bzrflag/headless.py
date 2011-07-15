# Bzrflag
# Copyright 2008-2011 Brigham Young University
#
# This file is part of Bzrflag.
#
# Bzrflag is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Bzrflag is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Bzrflag.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of Bzrflag, please contact the Copyright
# Licensing Office, Brigham Young University, 3760 HBLL, Provo, UT 84602,
# (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

"""headless.py

Defines an Input class for a headless station.

"""
__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import asyncore
import logging

import server
import config
import constants  

logger = logging.getLogger('headless.py')


class Input:
    """The server input class."""
    
    def __init__(self, game):
        self.game = game
        self.servers = {}
        for color,team in self.game.map.teams.items():
            port_arg = ('0.0.0.0', game.config[color+'_port'])
            self.servers[color] = server.Server(port_arg, team, game.config)
            port = self.servers[color].get_port()
            if not game.config['test']:
                print 'port for %s: %s' % (color, port)

    def update(self):
        asyncore.loop(constants.LOOP_TIMEOUT, count = 1)
        
        
        
