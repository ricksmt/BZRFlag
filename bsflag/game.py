"""Game Logic

The Game Logic module implements teams, tanks, shots, etc.
"""

from __future__ import division

# TODO: Allow shots to be dynamically created and expired.  Make the objects
# aware of each other and implement collision detection.  Add flags and
# scoring.

import datetime
import math
import random

import constants


class Game(object):
    """Takes a list of colors."""
    def __init__(self, colors):
        self.teams = [Team(color) for color in colors]
        self.timestamp = datetime.datetime.utcnow()

    def update(self):
        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now

        dt = ((24 * 60 * 60) * delta.days
                + delta.seconds
                + (10 ** -6) * delta.microseconds)
        for team in self.teams:
            team.update(dt)


class Team(object):
    def __init__(self, color):
        self.color = color
        self.tanks = [Tank(color) for i in xrange(4)]
        self.shots = [Shot(color) for i in xrange(20)]

    def color_name(self):
        return constants.COLOR_NAME[self.color]

    def update(self, dt):
        for shot in self.shots:
            shot.update(dt)
        for tank in self.tanks:
            tank.update(dt)

    def shoot(self, tankid):
        pass

    def angvel(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].angvel = value


class Shot(object):
    size = (constants.ShotRadius,) * 2

    def __init__(self, color):
        self.color = color
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)

    def update(self, dt):
        # Update position.
        speed = constants.ShotSpeed
        # Temporary: make shots easier to see by slowing them down:
        speed /= 3
        dx = speed * dt * math.cos(self.rot)
        dy = speed * dt * math.sin(self.rot)
        x, y = self.pos
        self.pos = (x + dx), (y + dy)


class Tank(object):
    size = (constants.TankRadius,) * 2

    def __init__(self, color):
        self.color = color
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        self.angvel = 0

    def update(self, dt):
        # Update rotation.
        self.rot += self.angvel * constants.TankAngVel * dt

        # Update position.
        #x, y = self.pos
        #self.pos = (x + 1), y


# vim: et sw=4 sts=4
