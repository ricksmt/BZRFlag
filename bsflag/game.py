import math
import random

import constants


class Team(object):
    def __init__(self, color):
        self.tanks = [Tank(color) for i in xrange(5)]

    def __iter__(self):
        return iter(self.tanks)

    def update(self):
        for tank in self.tanks:
            tank.update()

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
    color = 1
    size = (constants.ShotRadius,) * 2
    pos = (-400, 0)
    rot = None

    def update(self):
        x, y = self.pos
        self.pos = (x + 1), y


class Tank(object):
    size = (constants.TankRadius,) * 2

    def __init__(self, color):
        self.color = color
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        self.angvel = 0

    def update(self):
        # Update rotation.
        self.rot += self.angvel * constants.TankAngVel

        # Update position.
        #x, y = self.pos
        #self.pos = (x + 1), y


# vim: et sw=4 sts=4
