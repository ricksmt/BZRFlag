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

    def iter_collisions(self):
        pass

    def wall_collisions(self):
        pass

    def distance(self, x1, y1, x2, y2):
        """Determines the distance between two points.

        Returns the calculated distance."""
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)

    def circle_intersect_circle(self, x1, y1, r1, x2, y2, r2):
        """Determines if a circle intersects a given circle or not."""
        inside = False
        dist = self.distance(x1, y1, x2, y2)
        if dist < (r1 + r2):
            inside = True
        return inside

    def circle_intersect_polygon(self, x, y, r, poly):
        """Determines if a circle intersects a given polygon or not.

        Polygon is a list of (x,y) pairs.
        """
        dist = 0
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(1, n + 1):
            p2x, p2y = poly[i % n]

            A = x - p1x
            B = y - p1y
            C = p2x - p1x
            D = p2y - p1y

            dot = A * C + B * D
            len_sq = C * C + D * D
            param = dot / len_sq

            xx, yy = 0, 0
            if param < 0:
                xx = p1x
                yy = p1y
            elif param > 1:
                xx = p2x
                yy = p2y
            else:
                xx = p1x + param * C
                yy = p1y + param * D

            dist = self.distance(x,y,xx,yy)

            if dist < r:
                inside = True
                #print "Collision"
                #print x, y
                #print p1x, p1y
                #print p2x, p2y
                return inside

            p1x, p1y = p2x, p2y

        return inside

    def point_inside_polygon(self, x, y, poly):
        """Determines if a point is inside a given polygon or not.

        Polygon is a list of (x,y) pairs.
        """
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) \
                                / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside


    def iter_shots(self):
        for team in self.teams:
            for shot in team.shots:
                yield shot

    def iter_flags(self):
        for team in self.teams:
            yield team.flag

    def iter_teams(self):
        for team in self.teams:
            yield team

    def iter_boxes(self):
        for item in self.world.boxes:
            yield item

    def lst_boxes(self):
        boxes = []
        for item in self.world.boxes:
            boxes.append(item)
        return boxes

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
        self.shots = []
        #self.flag = Flag(color, self.tanks[1])
        self.flag = Flag(color, None)

    def color_name(self):
        return constants.COLORNAME[self.color]

    def update(self, dt):
        for shot in self.shots:
            remove = shot.update(dt)
            if remove:
                self.shots.remove(shot)
        for tank in self.tanks:
            tank.update(dt)
        self.flag.update(dt)

    def iter_tanks(self):
        for tank in self.tanks:
            yield tank

    def shoot(self, tankid):
        tank = self.tanks[tankid]
        shot = Shot(tank)
        self.shots.insert(0, shot)

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

    def __init__(self, tank):
        self.color = tank.color
        self.game = tank.game
        self.rot = tank.rot
        self.pos = tank.pos
        speed = constants.SHOTSPEED
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))

    def update(self, dt):
        x, y = self.pos
        vx, vy = self.vel

        newx, newy = (x + vx * dt), (y + vy * dt)

        box_list = self.game.lst_boxes()

        collision_detected = False

        for item in box_list:
            poly = []
            for corner in self.game.iter_corners(item):
                poly.append(corner)
            if self.game.circle_intersect_polygon(newx, \
                newy, constants.SHOTRADIUS, poly):
                collision_detected = True
            elif self.game.point_inside_polygon(newx, newy, poly):
                collision_detected = True
        if not collision_detected:
            self.pos = newx, newy

        return collision_detected


class Flag(object):
    size = (constants.FLAGRADIUS,) * 2

    def __init__(self, color, tank):
        self.color = color
        self.rot = 0
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.tank = None
        if tank is not None:
            self.tank = tank

    def update(self, dt):
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos


class Tank(object):
    size = (constants.TANKRADIUS,) * 2

    def __init__(self, color, game):
        self.color = color
        self.game = game
        # For testing obstacle corners
        # TODO: remove and replace with proper unit test
        #self.pos = (-40, 360)
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        self.speed = 0
        self.vel = (0, 0)
        self.angvel = 0
        self.callsign = constants.COLORNAME[color]
        self.status = 'alive'
        self.shotsleft = -1
        self.reloadtime = 0
        self.flag = '-'

    def update(self, dt):
        # Update rotation.
        self.rot += self.angvel * constants.TANKANGVEL * dt

        # Update position.
        # TODO: account for acceleration and collision detection
        x, y = self.pos
        self.vel = (self.speed * math.cos(self.rot) * constants.TANKSPEED, 
            self.speed * math.sin(self.rot) * constants.TANKSPEED)
        vx, vy = self.vel
        newx, newy = (x + vx * dt), (y + vy * dt)

        box_list = self.game.lst_boxes()

        collision_detected = False

        for item in box_list:
            poly = []
            for corner in self.game.iter_corners(item):
                poly.append(corner)
            if self.game.circle_intersect_polygon(newx, \
                newy, constants.TANKRADIUS, poly):
                collision_detected = True
        if not collision_detected:
            self.pos = newx, newy

# vim: et sw=4 sts=4
