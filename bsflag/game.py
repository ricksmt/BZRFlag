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
    def __init__(self, colors, world):
        self.teams = [Team(color, self) for color in colors]
        self.world = world
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

    def iter_shots(self):
        for team in self.teams:
            for shot in team.shots:
                yield shot

    def iter_teams(self):
        for team in self.teams:
            yield team

    def iter_boxes(self):
        for item in self.world.boxes:
            yield item

    def iter_bases(self):
        for item in self.world.bases:
            yield item

    def iter_corners(self, item):
        x = int(item.pos.asList()[0])
        y = int(item.pos.asList()[1])
        if item.pos:
            w = int(item.size.asList()[0])
            h = int(item.size.asList()[1])
        else:
            w, h = 0
        # Implemented for rectangles
        for i in xrange(4):
            if i == 0: a, b = w * -1, h
            elif i == 1: a, b = w * -1, h * -1
            elif i == 2: a, b = w, h * -1
            elif i == 3: a, b = w, h 
            else: a, b = 0
            yield (int(a * math.cos(item.rot) - b * math.sin(item.rot)) + x, 
                int(a * math.sin(item.rot) + b * math.cos(item.rot)) + y)


class Team(object):
    def __init__(self, color, game):
        self.color = color
        self.game = game
        self.tanks = [Tank(color, game) for i in xrange(4)]
        self.shots = [Shot(color, game) for i in xrange(20)]

    def color_name(self):
        return constants.COLORNAME[self.color]

    def update(self, dt):
        for shot in self.shots:
            shot.update(dt)
        for tank in self.tanks:
            tank.update(dt)

    def iter_tanks(self):
        for tank in self.tanks:
            yield tank

    def shoot(self, tankid):
        pass

    def speed(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].speed = value

    def angvel(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].angvel = value


class Shot(object):
    size = (constants.SHOTRADIUS,) * 2

    def __init__(self, color, game):
        self.color = color
        self.game = game
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        speed = constants.SHOTSPEED
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))

    def update(self, dt):
        x, y = self.pos
        vx, vy = self.vel
        self.pos = (x + vx * dt), (y + vy * dt)


class Tank(object):
    size = (constants.TANKRADIUS,) * 2

    def __init__(self, color, game):
        self.color = color
        self.game = game
        # For testing obstacle corners
        # TODO: remove and replace with proper unit test
        self.pos = (-40, 360)
        #self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        self.speed = 0
        self.vel = (0, 0)
        self.angvel = 0

    def update(self, dt):
        # Update rotation.
        self.rot += self.angvel * constants.TANKANGVEL * dt

        # Update position.
        # TODO: account for acceleration and collision detection
        x, y = self.pos
        self.vel = (self.speed * math.cos(self.rot) * constants.TANKSPEED, 
            self.speed * math.sin(self.rot) * constants.TANKSPEED)
        vx, vy = self.vel
        self.pos = (x + vx * dt), (y + vy * dt)


# vim: et sw=4 sts=4
