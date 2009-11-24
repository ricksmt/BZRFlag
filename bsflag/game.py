"""Game Logic

The Game Logic module implements teams, tanks, shots, etc.
"""

from __future__ import division

# TODO:
import asyncore
import copy
import datetime
import math
import random
import sys
import pygame
from pygame.locals import *

import constants

# A higher loop timeout decreases CPU usage but also decreases the frame rate.
LOOP_TIMEOUT = 0.01


class Game(object):
    """Takes a config Values object and a World object."""
    def __init__(self, config, world):
        self.mapper = Mapper(config, world)
        self.timespent = 0.0
        self.timelimit = 300000.0
        self.running = False
        self.mapper.timespent = self.timespent
        self.mapper.timelimit = self.timelimit
        self.timestamp = datetime.datetime.utcnow()

    def update(self):
        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now

        dt = ((24 * 60 * 60) * delta.days
                + delta.seconds
                + (10 ** -6) * delta.microseconds)

        self.timespent = self.timespent + dt
        if self.timespent > self.timelimit:
            return
        self.mapper.timespent = self.timespent

        for team in self.mapper.teams:
            team.update(dt)

    def events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

    def loop(self,display):
        self.running = True
        while self.running:
            asyncore.loop(LOOP_TIMEOUT, count=1)
            # TODO: clean this up
            # shottemp = 0
            # tanktemp = 0

            #for team in game.mapper.teams:
            #    shottemp = shottemp + len(team.shots)
            #    tanktemp = tanktemp + len(team.tanks)

            #if shottemp > shotcount:
            #    for team in game.mapper.teams:
            #        for shot in team.shots:
            #            display.shot_sprite(shot)
            #if tanktemp > tankcount:
            #    for team in game.mapper.teams:
            #        for tank in team.tanks:
            #            display.tank_sprite(tank)
            self.events()

            self.update()

            while len(self.mapper.inbox) > 0:
                obj = self.mapper.inbox.pop()
                if isinstance(obj, Tank):
                    display.tank_sprite(obj)
                elif isinstance(obj, Shot):
                    display.shot_sprite(obj)
                elif isinstance(obj, Flag):
                    display.flag_sprite(obj)

            while len(self.mapper.trash) > 0:
                obj = self.mapper.trash.pop()
                display.kill_sprite(obj)

            display.update()

class Mapper(object):
    def __init__(self, config, world):
        # track objects on map
        self.obstacles = [Obstacle(item) for item in world.boxes]
        self.bases = [Base(item) for item in world.bases]

        self.teams = []
        for color in ('red','green','blue','purple'):
            if config[color+'_port'] is not None:
                self.teams.append(Team(self, color, config))
        #self.teams = [Team(item, self) for item in bzrobots.teams]
        for team in self.teams:
            self.spawn_flag(team.flag)
        for team in self.teams:
            for enemy in self.teams:
                #if enemy == team:continue
                team.score_map[enemy.color] = Score(team, enemy)

        # defaults for customizable values
        world_diagonal = constants.WORLDSIZE * math.sqrt(2.0)
        max_bullet_life = constants.WORLDSIZE / constants.SHOTSPEED
        self.maximum_shots = int(max_bullet_life / constants.RELOADTIME)
        self.timespent = 0.0
        self.timelimit = 0.0
        self.inertia_linear = 1
        self.inertia_angular = 1
        self.tank_angvel = constants.TANKANGVEL
        self.max_tanks = 0.0
        for team in self.teams:
            self.max_tanks = float(max(len(team.tanks), self.max_tanks))
        self.respawn_time = 10
        self.range = constants.SHOTRANGE
        self.grab_own_flag = False
        self.friendly_fire = False
        self.hoverbot = 0
        self.end_game = False

        # queue of objects that need to be created or destroyed
        self.inbox = []
        self.trash = []

    def spawn_tank(self, tank):
        """Creates a tank at its respective base.

        The tank is placed at a random location within a certain radius from
        the center of the base. This radius is based on the number of tanks
        and the radius of individual tanks (i.e. the area occupied by tanks).
        """
        color = tank.color
        base = None
        for team_base in self.bases:
            if team_base.color == color:
                base = team_base
        assert base != None
        base_x, base_y = base.center
        spawn_radius = constants.TANKRADIUS * math.sqrt(self.max_tanks) * 5
        candidate_obstacles = []

        for obstacle in self.obstacles:
            assert isinstance(obstacle, Obstacle)
            obstacle_x, obstacle_y = obstacle.center
            if (self.distance(base_x, base_y, obstacle_x, obstacle_y) \
                    - obstacle.radius) <= spawn_radius:
                padded_obstacle = copy.deepcopy(obstacle)
                padded_obstacle.pad(constants.TANKRADIUS * 1.5)
                candidate_obstacles.append(padded_obstacle)

        tank_radius = constants.TANKRADIUS
        shot_radius = constants.SHOTRADIUS
        tank_x = 0
        tank_y = 0
        placed = False
        while placed == False:
            angle = random.uniform(0, 2 * math.pi)
            offset = random.uniform(0, 1)
            tank_x = base_x + spawn_radius * offset * math.cos(angle)
            tank_y = base_y + spawn_radius * offset * math.sin(angle)
            tank_pos = (tank_x, tank_y)

            if (abs(tank_x) > 400) or (abs(tank_y) > 400):
                continue

            placed = True
            for obst in candidate_obstacles:
                if self.point_inside_polygon(tank_x, tank_y, obst.corners):
                    placed = False
                    break
            if placed == False:
                continue
            for team in self.teams:
                for other_tank in team.tanks:
                    if self.circle_intersect_circle(tank_pos, other_tank.pos,
                            tank_radius, tank_radius):
                        placed = False
                        break
                if placed == False:
                    break
                for shot in team.shots:
                    if self.circle_intersect_circle(tank_pos, shot.pos,
                            tank_radius, shot_radius):
                        placed = False
                        break
                if placed == False:
                    break

        tank.pos = (tank_x, tank_y)
        tank.rot = random.uniform(0, 2 * math.pi)
        tank.status = constants.TANKALIVE

    def spawn_flag(self, flag):
        """Places flag in middle of respective base."""
        for base in self.bases:
            if flag.color == base.color:
                flag.pos = base.center

    def handle_collisions(self, obj, dt):
        """Handles the collision detecting process for a given object.

        The obj parameter is the object, while the dt is the time elapsed
        since collisions were last handled for this object. As a result of
        calling this method, the object's new position and status (alive,
        dead, etc.) are set.
        """
        candidate_obstacles = []
        pos = obj.pos
        x, y = pos
        obj_radius = 0.0
        if isinstance(obj, Flag):
            # shameless winning, fix this stuff
            for base in self.bases:
                if base.color != obj.color \
                        and obj.tank != None \
                        and base.color == obj.tank.color \
                        and self.point_inside_polygon(x, y, base.corners):
                    for team in self.teams:
                        if team.color == obj.color:
                            team.loser = True
                            for tank in team.tanks:
                                tank.status = constants.TANKDEAD
                                tank.dead_timer = 0
                        elif team.color == base.color:
                            team.captured_flags.append(obj)
                            score = team.score_map[obj.color]
                            score.returned_flag = True
                            enemy = score.enemy
                            enemy.loser = True
            return
        elif isinstance(obj, Tank):
            obj_radius = constants.TANKRADIUS
            if obj.status == constants.TANKDEAD:
                obj.pos = (constants.DEADZONEX, constants.DEADZONEY)
                for team in self.teams:
                    if team.color == obj.color and team.loser == True:
                        obj.dead_timer = 0
                return
        elif isinstance(obj, Shot):
            obj_radius = constants.SHOTRADIUS
            shot_x, shot_y = obj.pos
            if (abs(shot_x) > 400) or (abs(shot_y) > 400):
                obj.status = constants.SHOTDEAD
                return
        else:
            # TODO: error
            print 'error'
        vel = obj.vel
        multisample = self.lst_pos_samples(pos, vel, obj_radius, dt)

        # TODO: merely functional, needs to be fixed badly
        for sample in multisample:
            sample_x, sample_y = sample
            if (abs(sample_x) > 399) or (abs(sample_y) > 399):
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
                    if good_pos == (constants.DEADZONEX, constants.DEADZONEY):
                        break
            if good_pos == (constants.DEADZONEX, constants.DEADZONEY):
                break
            for shot in team.shots:
                shot_x, shot_y = shot.pos
                if (self.distance(mid_x, mid_y, shot_x, shot_y) \
                        - constants.SHOTRADIUS - obj_radius) <= filter_radius:
                    good_pos = self.handle_shot_collision(obj, good_pos, shot)
                    if good_pos == (constants.DEADZONEX, constants.DEADZONEY):
                        break
            if good_pos == (constants.DEADZONEX, constants.DEADZONEY):
                break
            flag_x, flag_y = team.flag.pos
            if (self.distance(mid_x, mid_y, flag_x, flag_y) \
                    - constants.FLAGRADIUS - obj_radius) <= filter_radius:
                good_pos = self.handle_flag_collision(obj, good_pos,
                    team.flag)

        if (isinstance(obj, Shot)):
            good_x, good_y = good_pos
            range_expended = self.distance(x, y, good_x, good_y)
            obj.distance = float(obj.distance + range_expended)
        obj.pos = good_pos

    def midpoint(self, x1, y1, x2, y2):
        """Determines the midpoint of a line segment.

        >>> mock_bzrobots = SimpleMock()
        >>> mock_world = SimpleMock()
        >>> mock_world.boxes = []
        >>> mock_world.bases = []
        >>> mock_bzrobots.teams = []
        >>> maptest = Mapper(mock_bzrobots, mock_world)
        >>> maptest.midpoint(0, 0, 0, 0)
        (0.0, 0.0)
        >>> maptest.midpoint(1, 1, 1, 3)
        (1.0, 2.0)
        >>>
        """
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        return (mid_x, mid_y)

    def distance(self, x1, y1, x2, y2):
        """Determines the distance between two points.

        Returns the calculated distance.

        >>> mock_bzrobots = SimpleMock()
        >>> mock_world = SimpleMock()
        >>> mock_world.boxes = []
        >>> mock_world.bases = []
        >>> mock_bzrobots.teams = []
        >>> maptest = Mapper(mock_bzrobots, mock_world)
        >>> maptest.distance(0, 0, 0, 0)
        0.0
        >>> maptest.distance(1, -2, 4, -6)
        5.0
        >>>
        """
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_line(self, point, line):
        """Determines the shortest distance between a point and a line
        segment.
        """
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
        """Determines if a circle intersects a given circle or not.

        >>> mock_bzrobots = SimpleMock()
        >>> mock_world = SimpleMock()
        >>> mock_world.boxes = []
        >>> mock_world.bases = []
        >>> mock_bzrobots.teams = []
        >>> maptest = Mapper(mock_bzrobots, mock_world)
        >>> maptest.circle_intersect_circle((0, 0), (0, 0), 0, 0)
        False
        >>> maptest.circle_intersect_circle((1, 2), (4, 2), 1, 3)
        True
        >>>
        """
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
        """Called when one object in a collision has been identified as a
        tank. Handles the cases for a tank collision with other moveable
        objects.
        """
        if obj == tank:
            return new_pos

        if isinstance(obj, Tank):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(tank.pos, path)
            if dist < (constants.TANKRADIUS + constants.TANKRADIUS):
                #print 'tank on tank'
                return obj.pos
        elif isinstance(obj, Shot):
            # Prevents tank from killing self
            if obj.tank == tank:
                return new_pos
            elif obj.color == tank.color and self.friendly_fire == False:
                return new_pos
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(tank.pos, path)
            if dist < (constants.SHOTRADIUS + constants.TANKRADIUS):
                #print 'shot on tank'
                # TODO: fix, very inefficient
                if tank.flag != None:
                    for team in self.teams:
                        if team.color == tank.color:
                            team.flag_carriers.remove(tank)
                    tank.flag.tank = None
                    tank.flag = None
                obj.status = constants.SHOTDEAD
                tank.status = constants.TANKDEAD
                tank.dead_timer = 0
                tank.pos = (constants.DEADZONEX, constants.DEADZONEY)
                return obj.pos

        return new_pos

    def handle_shot_collision(self, obj, new_pos, shot):
        if obj == shot:
            return new_pos

        if isinstance(obj, Tank):
            # Prevents tank from killing self
            if shot.tank == obj:
                return new_pos
            elif shot.color == obj.color and self.friendly_fire == False:
                return new_pos
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(shot.pos, path)
            if dist < (constants.TANKRADIUS + constants.SHOTRADIUS):
                #print 'tank on shot'
                # TODO: fix, very inefficient
                if obj.flag != None:
                    for team in self.teams:
                        if team.color == obj.color:
                            team.flag_carriers.remove(obj)
                    obj.flag.tank = None
                    obj.flag = None
                obj.status = constants.TANKDEAD
                obj.dead_timer = 0
                shot.status = constants.SHOTDEAD
                obj.pos = (constants.DEADZONEX, constants.DEADZONEY)
                return obj.pos

        return new_pos

    def handle_flag_collision(self, obj, new_pos, flag):
        if (obj == flag) or (obj.color == flag.color):
            return new_pos

        if isinstance(obj, Tank):
            path = [obj.pos, new_pos]
            dist = self.distance_to_line(flag.pos, path)
            if dist < (constants.TANKRADIUS + constants.FLAGRADIUS):
                #print 'tank on flag'
                obj.flag = flag
                flag.tank = obj
                # TODO: fix, very inefficient
                for team in self.teams:
                    for tank in team.tanks:
                        if tank.flag == flag:
                            team.flag_carriers.append(tank)

        return new_pos

    def lst_pos_samples(self, pos, vel, r, dt):
        """Returns a list of valid samples along the proposed object path.
        """
        samples = []
        x, y = pos
        vx, vy = vel
        endx, endy = (x + vx * dt), (y + vy * dt)

        segment = r / 2.0
        if segment == 0:
            print 'error'

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
        self.rot = item.rot
        self.corners = self.lst_corners()

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

    def lst_corners(self):
        # TODO: and clean this too
        corners = []
        x, y = self.center
        w, h = self.size
        # Implemented for rectangles
        for i in xrange(4):
            if i == 0: a, b = w * -1, h
            elif i == 1: a, b = w * -1, h * -1
            elif i == 2: a, b = w, h * -1
            elif i == 3: a, b = w, h
            else: a, b = 0
            corners.append((a * math.cos(self.rot)
                - b * math.sin(self.rot) + x,
                a * math.sin(self.rot) + b * math.cos(self.rot) + y))
        return corners

    def pad(self, padding):
        w, h = self.size
        self.size = (w + padding, h + padding)
        self.corners = self.lst_corners()


class Team(object):
    def __init__(self, mapper, color, config):
        self.color = ['rogue','red','green','blue','purple'].index(color)
        self.colorname = color
        self.mapper = mapper
        if not config[color+'_tanks']:
            config[color+'_tanks'] = 10
        if not config[color+'_port']:
            config[color+'_port'] = 0
        self.port = config[color+'_port']
        print [self.port]
        self.tanks = [Tank(self.color, i) for i in xrange(int(config[color+'_tanks']))]
        self.shots = []
        self.flag = Flag(self.color, None)
        self.flag_carriers = []
        self.captured_flags = []
        self.loser = False
        self.score_map = {}
        self.base = None
        for base in mapper.bases:
            if base.color != self.color:
                continue
            else:
                self.base = base
                break
        self.posnoise = 0.0
        if config[color+'_posnoise']:
            self.posnoise = config[color+'_posnoise']
        self.angnoise = 0.0
        if config[color+'_angnoise']:
            self.angnoise = config[color+'_angnoise']
        self.velnoise = 0.0
        if config[color+'_velnoise']:
            self.velnoise = config[color+'_velnoise']

    def iter_score(self):
        for team in self.mapper.teams:
            yield self.score_map[team.color]

    def iter_ctf_scores(self):
        for team in self.mapper.teams:
            yield self.score_map[team.color].ctf_score()

    def color_name(self):
        return constants.COLORNAME[self.color]

    def update(self, dt):
        for shot in self.shots:
            shot.update(self.mapper, dt)
        for tank in self.tanks:
            tank.update(self.mapper, dt)
        self.flag.update(self.mapper, dt)
        for score in self.iter_score():
            score.update(self.mapper)

    def iter_tanks(self):
        for tank in self.tanks:
            yield tank

    def shoot(self, tankid):
        tank = self.tanks[tankid]
        if (tank.reloadtime < constants.RELOADTIME) or \
                ((self.mapper.maximum_shots - len(tank.shots)) == 0):
            return False
        shot = Shot(tank)
        self.shots.insert(0, shot)
        self.mapper.inbox.append(shot)
        tank.reloadtime = 0
        return True

    def speed(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].given_speed = value

    def angvel(self, tankid, value):
        # TODO: care about list bounds.
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tanks[tankid].given_angvel = value


class Score(object):
    def __init__(self, team, enemy):
        self.team = team
        self.enemy = enemy
        self.returned_flag = False
        self.dist_with_flag = 0
        self.dist_to_flag = sys.maxint
        self.enemy_with_flag = 0
        self.kills = 0

    def update(self, mapper):
        if self.returned_flag == True or self.team.loser == True:
            return
        if self.team.color == self.enemy.color:
            return
        tank = None
        for carrier in self.team.flag_carriers:
            if carrier.flag == None or \
                    carrier.flag.color != self.enemy.color:
                continue
            else:
                tank = carrier
                break
        if tank != None:
            flag_x, flag_y = tank.flag.pos
            base_x, base_y = self.team.base.center
            enemy_x, enemy_y = self.enemy.base.center
            dist_between_bases = mapper.distance(base_x, base_y,
                enemy_x, enemy_y)
            dist_with_flag = dist_between_bases - \
                mapper.distance(flag_x, flag_y, base_x, base_y)
            #print ('%s %s' % (self.dist_with_flag, dist_with_flag))
            self.dist_with_flag = max(self.dist_with_flag, dist_with_flag)
        else:
            flag_x, flag_y = self.enemy.flag.pos
            for tank in self.team.tanks:
                tank_x, tank_y = tank.pos
                dist_to_flag = mapper.distance(flag_x, flag_y, tank_x, tank_y)
                self.dist_to_flag = min(self.dist_to_flag, dist_to_flag)
        enemy_with_flag = self.enemy.score_map[self.team.color].dist_with_flag
        self.enemy_with_flag = enemy_with_flag

    def ctf_score(self):
        score = 0
        if self.team.color == self.enemy.color:
            return score
        elif self.returned_flag == True:
            score = constants.CAPTUREPOINTS
            return score
        elif self.team.loser == False:
            score = constants.INITPOINTS
            #print('%s' % (self.dist_with_flag))
            score = score + self.dist_with_flag - self.dist_to_flag - \
            self.enemy_with_flag
        return int(score)


class Shot(object):
    size = (constants.SHOTRADIUS,) * 2

    def __init__(self, tank):
        self.tank = tank
        self.color = self.tank.color
        self.rot = self.tank.rot
        self.distance = 0
        self.tank.shots.append(self)

        #tank_x, tank_y = tank.pos
        #x = tank_x + constants.BARRELLENGTH * math.cos(self.rot)
        #y = tank_y + constants.BARRELLENGTH * math.sin(self.rot)
        #self.pos = (x, y)
        self.pos = tank.pos

        speed = constants.SHOTSPEED + tank.speed
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))

        self.status = constants.SHOTALIVE

    def update(self, mapper, dt):
        mapper.handle_collisions(self, dt)
        if self.distance > constants.SHOTRANGE:
            self.status = constants.SHOTDEAD
        if self.status == constants.SHOTDEAD:
            mapper.trash.append(self)
            self.tank.shots.remove(self)
            for team in mapper.teams:
                if team.color == self.color:
                    team.shots.remove(self)


class Flag(object):
    size = (constants.FLAGRADIUS,) * 2

    def __init__(self, color, tank):
        self.color = color
        self.rot = 0
        self.pos = (constants.DEADZONEX, constants.DEADZONEY)
        self.tank = None
        if tank is not None:
            self.tank = tank

    def update(self, mapper, dt):
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos
        mapper.handle_collisions(self, dt)


class Base(object):
    def __init__(self, item):
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

    def __init__(self, color, tankid):
        self.color = color
        self.pos = (constants.DEADZONEX, constants.DEADZONEY)
        self.rot = 0
        self.speed = 0
        self.given_speed = 0
        self.vel = (0, 0)
        self.given_angvel = 0
        self.angvel = 0
        self.callsign = constants.COLORNAME[color] + str(tankid)
        self.status = constants.TANKDEAD
        self.shots = []
        self.reloadtime = 0
        self.flag = None
        self.dead_timer = -1

    def update(self, mapper, dt):
        if self.status == constants.TANKDEAD:
            if self.dead_timer < 0:
                self.dead_timer = mapper.respawn_time
            self.dead_timer = self.dead_timer + dt
            if self.dead_timer >= mapper.respawn_time:
                mapper.spawn_tank(self)
                return

        # Increment reload time
        if self.reloadtime < constants.RELOADTIME:
            self.reloadtime = self.reloadtime + dt

        # Update rotation.
        if self.angvel < self.given_angvel:
            self.angvel = self.angvel + constants.ANGULARACCEL * dt
            if self.angvel > self.given_angvel:
                self.angvel = self.given_angvel
        elif self.angvel > self.given_angvel:
            self.angvel = self.angvel - constants.ANGULARACCEL * dt
            if self.angvel < self.given_angvel:
                self.angvel = self.given_angvel
        self.rot += self.angvel * constants.TANKANGVEL * dt

        # Update position.
        x, y = self.pos
        if self.speed < self.given_speed:
            self.speed = self.speed + constants.LINEARACCEL * dt
            if self.speed > self.given_speed:
                self.speed = self.given_speed
        elif self.speed > self.given_speed:
            self.speed = self.speed - constants.LINEARACCEL * dt
            if self.speed < self.given_speed:
                self.speed = self.given_speed
        self.vel = (self.speed * math.cos(self.rot) * constants.TANKSPEED,
            self.speed * math.sin(self.rot) * constants.TANKSPEED)

        mapper.handle_collisions(self, dt)

        if (self.status == constants.TANKDEAD) and (self.flag != None):
            self.flag.tank = None
            self.flag = None


class SimpleMock(object):
    pass

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
