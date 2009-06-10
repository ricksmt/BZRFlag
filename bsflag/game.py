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
        self.mapper = Mapper(colors, world)
        self.timestamp = datetime.datetime.utcnow()

    def update(self):
        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now

        dt = ((24 * 60 * 60) * delta.days
                + delta.seconds
                + (10 ** -6) * delta.microseconds)
        for team in self.mapper.teams:
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
        x = item.pos.asList()[0]
        y = item.pos.asList()[1]
        if item.pos:
            w = item.size.asList()[0]
            h = item.size.asList()[1]
        else:
            w, h = 0
        # Implemented for rectangles
        for i in xrange(4):
            if i == 0: a, b = w * -1, h
            elif i == 1: a, b = w * -1, h * -1
            elif i == 2: a, b = w, h * -1
            elif i == 3: a, b = w, h 
            else: a, b = 0
            yield (a * math.cos(item.rot) - b * math.sin(item.rot) + x, 
                a * math.sin(item.rot) + b * math.cos(item.rot) + y)


class Mapper(object):
    def __init__(self, colors, world):
        self.teams = [Team(color, self) for color in colors]
        self.bases = [Base(color, item) for item in world.bases]
        self.obstacles = [Obstacle(item) for item in world.boxes]
        self.inbox = []
        self.trash = []

    def handle_collisions(self, obj, dt):
        # generate all position samples
        # using last position (destination), calculate maximum distance
        # compare distance (plus radius) against objects in this order:
        #   obstacles
        #   tanks
        #   bullets
        #   flags
        # if the radius of both objects added together is less than or equal 
        # to the maximum distance, add the object to the appropriate list
        # as a potential collision
        # (if not, then it is impossible to have a collision)
        # starting with obstacles, check for each position sample colliding
        # once a collision is found, remove that position and all following
        # positions, so that the last position is the most recent valid
        # position
        # perform the same steps with other tanks (using the pruned list)
        # if the moving object is a tank, iteratively check the positions 
        # against bullets, changing the status of both tank and bullet to 
        # "dead" or "destroyed" (this will flag clean-up) if a collision is
        # detected
        # (at this point, checking for flag collisions would be unecessary)
        # if the moving object is a bullet, no checks are needed beyond tanks
        # a flag only needs to check if it is in a base of a different color
        # once all potential objects have been checked, the Map object changes
        # the status of the objects involved if needed and returns the new
        # valid position so the object can update itself
        candidate_obstacles = []
        pos = obj.pos
        x, y = pos
        obj_radius = 0.0
        if isinstance(obj, Flag):
            # shameless winning, fix this stuff
            for base in self.bases:
                if base.color != obj.color \
                        and self.point_inside_polygon(x, y, base.corners):
                    for team in self.teams:
                        if team.color != base.color:
                            for tank in team.tanks:
                                tank.status = constants.TANKDEAD
            return
                    
        elif isinstance(obj, Tank):
            obj_radius = constants.TANKRADIUS
        elif isinstance(obj, Shot):
            obj_radius = constants.SHOTRADIUS
        else:
            # TODO: error
            print 'error'
        vel = obj.vel
        multisample = self.lst_pos_samples(pos, vel, obj_radius, dt)

        # TODO: merely functional, needs to be fixed badly
        for sample in multisample:
            sample_x, sample_y = sample
            if (abs(sample_x) > 400) or (abs(sample_y) > 400):
                multisample.remove(sample)

        if len(multisample) == 0 and isinstance(obj, Shot):
            obj.status = constants.SHOTDEAD
        if len(multisample) == 0:
            return


        end_x, end_y = multisample[-1]
        mid_x, mid_y = self.midpoint(x, y, end_x, end_y)
        filter_radius = self.distance(x, y, mid_x, mid_y)

        for obstacle in self.obstacles:
            assert isinstance(obstacle, Obstacle)
            obstacle_x, obstacle_y = obstacle.center
            if (self.distance(mid_x, mid_y, obstacle_x, obstacle_y) \
                    - obstacle.radius - obj_radius) <= filter_radius:
                candidate_obstacles.append(obstacle)

        good_x = x
        good_y = y

        if len(candidate_obstacles) == 0:
            good_x = end_x
            good_y = end_y

        for obstacle in candidate_obstacles:
            i = 0
            while i < len(multisample):
                sample_x, sample_y = multisample[i]
                if not self.circle_intersect_polygon(sample_x, sample_y, 
                        obj_radius, obstacle.corners):
                    good_x = sample_x
                    good_y = sample_y
                else:
                    # clears remainder of list
                    while i < len(multisample):
                        multisample.pop()
                i += 1

        if isinstance(obj, Shot) and (good_x != end_x or good_y != end_y):
            obj.status = constants.SHOTDEAD

        good_pos = (good_x, good_y)

        for team in self.teams:
            mid_x, mid_y = self.midpoint(x, y, good_x, good_y)
            filter_radius = self.distance(x, y, mid_x, mid_y)

            for tank in team.tanks:
                tank_x, tank_y = tank.pos
                if (self.distance(mid_x, mid_y, tank_x, tank_y) \
                        - constants.TANKRADIUS - obj_radius) <= filter_radius:
                    good_pos = self.handle_tank_collision(obj, good_pos, tank)
            for shot in team.shots:
                shot_x, shot_y = shot.pos
                if (self.distance(mid_x, mid_y, shot_x, shot_y) \
                        - constants.SHOTRADIUS - obj_radius) <= filter_radius:
                    good_pos = self.handle_shot_collision(obj, good_pos, shot)
            flag_x, flag_y = team.flag.pos
            if (self.distance(mid_x, mid_y, flag_x, flag_y) \
                    - constants.FLAGRADIUS - obj_radius) <= filter_radius:
                good_pos = self.handle_flag_collision(obj, good_pos, 
                    team.flag)

        obj.pos = good_pos

    def midpoint(self, x1, y1, x2, y2):
        """Determines the midpoint of a line segment."""
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        return (mid_x, mid_y)

    def distance(self, x1, y1, x2, y2):
        """Determines the distance between two points.

        Returns the calculated distance."""
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_line(self, point, line):
        x, y = point
        start_x, start_y = line[0]
        end_x, end_y = line[1]
        A = x - start_x
        B = y - start_y
        C = end_x - start_x
        D = end_y - start_y

        dot = A * C + B * D
        len_sq = C * C + D * D
        param = 0
        if len_sq != 0:
            param = dot / len_sq

        xx, yy = 0, 0
        if param < 0:
            xx = start_x
            yy = start_y
        elif param > 1:
            xx = end_x
            yy = end_y
        else:
            xx = start_x + param * C
            yy = start_y + param * D

        dist = self.distance(x,y,xx,yy)
        return dist

    def circle_intersect_circle(self, pos1, pos2, r1, r2):
        """Determines if a circle intersects a given circle or not."""
        inside = False
        x1, y1 = pos1
        x2, y2 = pos2
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

            point = (x, y)
            line = [(p1x, p1y), (p2x, p2y)]

            dist = self.distance_to_line(point, line)

            if dist < r:
                inside = True
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

    def handle_tank_collision(self, obj, new_pos, tank):
        if obj == tank:
            return new_pos

        if isinstance(obj, Tank):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(tank.pos, path)
            if dist < (constants.TANKRADIUS + constants.TANKRADIUS):
                print 'tank on tank'
                return obj.pos
        elif isinstance(obj, Shot):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(tank.pos, path)
            if dist < (constants.SHOTRADIUS + constants.TANKRADIUS):
                print 'shot on tank'
                obj.status = constants.SHOTDEAD
                tank.status = constants.TANKDEAD
                return obj.pos

        return new_pos

    def handle_shot_collision(self, obj, new_pos, shot):
        if obj == shot:
            return new_pos

        if isinstance(obj, Tank):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(shot.pos, path)
            if dist < (constants.TANKRADIUS + constants.SHOTRADIUS):
                print 'tank on shot'
                obj.status = constants.TANKDEAD
                shot.status = constants.SHOTDEAD
                return obj.pos

        return new_pos

    def handle_flag_collision(self, obj, new_pos, flag):
        if (obj == flag) or (obj.color == flag.color):
            return new_pos

        if isinstance(obj, Tank):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(flag.pos, path)
            if dist < (constants.TANKRADIUS + constants.FLAGRADIUS):
                print 'tank on flag'
                obj.flag = flag
                flag.tank = obj

        return new_pos

    def lst_pos_samples(self, pos, vel, r, dt):
        """Returns a list of valid samples along the proposed object path.
        """
        samples = []
        x, y = pos
        vx, vy = vel
        endx, endy = (x + vx * dt), (y + vy * dt)

        segment = r / 2
        if segment < 1:
            segment = 1

        dx = x - endx
        dy = y - endy
        dist = math.sqrt(dx * dx + dy * dy)

        num_segments = int(dist / segment)
        if num_segments == 0:
            samples.append(((x + vx * dt), (y + vy * dt)))
        for i in xrange(num_segments):
            samples.append(((x + vx * dt * ((i + 1.0) / num_segments)), 
                (y + vy * dt * ((i + 1.0) / num_segments))))
        return samples

    def iter_flags(self):
        for team in self.teams:
            yield team.flag

    def iter_shots(self):
        for team in self.teams:
            for shot in team.shots:
                yield shot

    def iter_teams(self):
        for team in self.teams:
            yield team

class Obstacle(object):
    def __init__(self, item):
        self.center = self.get_center(item)
        self.size = self.get_size(item)
        self.radius = self.get_radius()
        self.corners = self.lst_corners(item)

    def get_center(self, item):
        # TODO: clean this
        x = item.pos.asList()[0]
        y = item.pos.asList()[1]
        return (x, y)

    def get_size(self, item):
        # TODO: and this
        w = item.size.asList()[0]
        h = item.size.asList()[1]
        return (w, h)

    def get_radius(self):
        w, h = self.size
        radius = math.sqrt(w * w + h * h)
        return radius

    def lst_corners(self, item):
        # TODO: and clean this too
        corners = []
        x, y = self.center
        if item.pos:
            w, h = self.size
        else:
            w, h = 0
        # Implemented for rectangles
        for i in xrange(4):
            if i == 0: a, b = w * -1, h
            elif i == 1: a, b = w * -1, h * -1
            elif i == 2: a, b = w, h * -1
            elif i == 3: a, b = w, h 
            else: a, b = 0
            corners.append((a * math.cos(item.rot)  
                - b * math.sin(item.rot) + x, 
                a * math.sin(item.rot) + b * math.cos(item.rot) + y))
        return corners


class Team(object):
    def __init__(self, color, mapper):
        self.color = color
        self.mapper = mapper
        self.tanks = [Tank(color) for i in xrange(20)]
        self.shots = [Shot(tank) for tank in self.tanks]
        self.flag = Flag(color, None)

    def color_name(self):
        return constants.COLORNAME[self.color]

    def update(self, dt):
        for shot in self.shots:
            shot.update(self.mapper, dt)
        for tank in self.tanks:
            tank.update(self.mapper, dt)
        self.flag.update(self.mapper, dt)

    def iter_tanks(self):
        for tank in self.tanks:
            yield tank

    def shoot(self, tankid):
        tank = self.tanks[tankid]
        shot = Shot(tank)
        self.shots.insert(0, shot)
        self.mapper.inbox.append(shot)

    def speed(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].givenspeed = value

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
        self.rot = tank.rot

        tank_x, tank_y = tank.pos
        x = tank_x + constants.BARRELLENGTH * math.cos(self.rot)
        y = tank_y + constants.BARRELLENGTH * math.sin(self.rot)
        self.pos = (x, y)

        speed = constants.SHOTSPEED
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))

        self.status = constants.SHOTALIVE

    def update(self, mapper, dt):        
        mapper.handle_collisions(self, dt)
        if self.status == constants.SHOTDEAD:
            mapper.trash.append(self)
            for team in mapper.teams:
                if team.color == self.color:
                    team.shots.remove(self)


class Flag(object):
    size = (constants.FLAGRADIUS,) * 2

    def __init__(self, color, tank):
        self.color = color
        self.rot = 0
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.tank = None
        if tank is not None:
            self.tank = tank

    def update(self, mapper, dt):
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos
        mapper.handle_collisions(self, dt)


class Base(object):
    def __init__(self, color, item):
        self.color = item.color
        self.center = self.get_center(item)
        self.size = self.get_size(item)
        self.radius = self.get_radius()
        self.corners = self.lst_corners(item)

    def get_center(self, item):
        # TODO: clean this
        x = item.pos.asList()[0]
        y = item.pos.asList()[1]
        return (x, y)

    def get_size(self, item):
        # TODO: and this
        w = item.size.asList()[0]
        h = item.size.asList()[1]
        return (w, h)

    def get_radius(self):
        w, h = self.size
        radius = math.sqrt(w * w + h * h)
        return radius

    def lst_corners(self, item):
        # TODO: and clean this too
        corners = []
        x, y = self.center
        if item.pos:
            w, h = self.size
        else:
            w, h = 0
        # Implemented for rectangles
        for i in xrange(4):
            if i == 0: a, b = w * -1, h
            elif i == 1: a, b = w * -1, h * -1
            elif i == 2: a, b = w, h * -1
            elif i == 3: a, b = w, h 
            else: a, b = 0
            corners.append((a * math.cos(item.rot)  
                - b * math.sin(item.rot) + x, 
                a * math.sin(item.rot) + b * math.cos(item.rot) + y))
        return corners

class Tank(object):
    size = (constants.TANKRADIUS,) * 2

    def __init__(self, color):
        self.color = color
        #self.game = game
        # For testing obstacle corners
        # TODO: remove and replace with proper unit test
        #self.pos = (-40, 360)
        self.pos = (random.uniform(-400, 400), random.uniform(-400, 400))
        self.rot = random.uniform(0, 2*math.pi)
        self.speed = 0
        self.givenspeed = 0
        self.vel = (0, 0)
        self.angvel = 0
        self.callsign = constants.COLORNAME[color]
        self.status = constants.TANKALIVE
        self.shotsleft = -1
        self.reloadtime = 0
        self.flag = None

    def update(self, mapper, dt):
        # Update rotation.
        self.rot += self.angvel * constants.TANKANGVEL * dt

        # Update position.
        x, y = self.pos
        if self.speed < self.givenspeed:
            self.speed = self.speed + constants.LINEARACCEL * dt
            if self.speed > self.givenspeed:
                self.speed = self.givenspeed
        elif self.speed > self.givenspeed:
            self.speed = self.speed - constants.LINEARACCEL * dt
            if self.speed < self.givenspeed:
                self.speed = self.givenspeed
        self.vel = (self.speed * math.cos(self.rot) * constants.TANKSPEED, 
            self.speed * math.sin(self.rot) * constants.TANKSPEED)

        mapper.handle_collisions(self, dt)

        if self.status == constants.TANKDEAD:
            mapper.trash.append(self)
            if self.flag != None:
                self.flag.tank = None
                self.flag = None
            for team in mapper.teams:
                if team.color == self.color:
                    team.tanks.remove(self)


# vim: et sw=4 sts=4
