"""BZFlag Constants

These constants are originally defined in src/common/global.cxx in the BZFlag
repository.  There are more than a hundred BZFlag constants that are in
global.cxx but are not included in the list of BSFlag constants.

"""

from __future__ import division
import math
import logging

logger = logging.getLogger('constants')

# Colors
COLORNAME = ('rogue', 'red', 'green', 'blue', 'purple')

# Tanks
TANKANGVEL = math.pi / 4
TANKLENGTH = 6
TANKRADIUS = 0.72 * TANKLENGTH
TANKSPEED = 25
LINEARACCEL = 0.5
ANGULARACCEL = 0.5
TANKWIDTH = 2.8
TANKALIVE = 'alive'
TANKDEAD = 'dead'
DEADZONE = -999999.0, -999999.0

# Shots
SHOTRADIUS = 0.5
SHOTRANGE = 350
SHOTSPEED = 100
RELOADTIME = SHOTRANGE / SHOTSPEED
SHOTALIVE = 'alive'
SHOTDEAD = 'dead'

# Flags
FLAGRADIUS = 2.5
INITPOINTS = 2000
CAPTUREPOINTS = 4000

# Rules
EXPLODETIME = 5

# Graphics
BASE_PATTERN = '%s_basetop.png'
SHOT_PATTERN = '%s_bolt.png'
FLAG_PATTERN = '%s_flag.png'
TANK_PATTERN = '%s_tank.png'
TILESCALE = 0.1
SHOTSCALE = 2
FLAGSCALE = 3
TANKSCALE = 1.2

FONTSIZE = 16

# A higher loop timeout decreases CPU usage but also decreases the frame rate.
LOOP_TIMEOUT = 0.01

# Server
BACKLOG = 5

# Game
RESPAWNTRIES = 1000



