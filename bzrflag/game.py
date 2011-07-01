import math
import random
import datetime
import numpy
import logging

import collide
import constants
from config import config

logger = logging.getLogger('game')


class GoodrichException(Exception):
    pass


class Game:
    """*Main control object. Contains the main loop.*

    Attributes:

    * map => :class:`game.Map`
    * input => :class:`headless.Input`
    * display => :class:`modpygame.Display`
    
    """
    
    def __init__(self):
    
        import headless #imported here to avoid circular imports
        import modpygame #imported here to avoid circular imports
        
        if config['random_seed'] != -1:
            random.seed(config['random_seed'])
        self.map = Map(self)
        self.display = modpygame.Display(self)
        self.input = headless.Input(self)
        self.running = False
        self.gameover = False
        self.timestamp = datetime.datetime.utcnow()

    def remake(self):
        """For testing purposes."""
        
        import modpygame #imported here to avoid circular imports
        
        self.display.kill()
        self.map = Map(self)
        self.display = modpygame.Display(self)
        self.running = False
        self.gameover = False
        self.timestamp = datetime.datetime.utcnow()

    def update(self):
        """Updates the game world."""
        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now
        dt = ((24 * 60 * 60) * delta.days
                + delta.seconds
                + (10 ** -6) * delta.microseconds)
        self.map.update(dt)

    def update_sprites(self):
        """Adds and removes sprites from the display."""
        while len(self.map.inbox) > 0:
            self.display.add_object(self.map.inbox.pop())
        while len(self.map.trash) > 0:
            self.display.remove_object(self.map.trash.pop())

    def loop(self):
        """The main loop of bzflag. checks events, updates positions,
        and draws to the screen until the pygame window is closed.
        
        """
        self.running = True
        self.display.setup()
        try:
            while self.running:
                if self.map.end_game:
                    # do something else here?
                    break
                self.input.update()
                self.update()
                self.update_sprites()
                self.display.update()
        except KeyboardInterrupt:
            pass
        finally:
            final_score = 'Final Score\n'
            for team in self.map.teams:
                final_score += 'Team %s: %d\n' % (team,
                                self.map.teams[team].score.total())
            print final_score

    def kill(self):
        self.running = False
        self.display.kill()


class Map(object):
    """Manages the map data. 
    
    Populates the current map with bases, obstacles, teams and tanks.
    
    """
    
    def __init__(self, game):
        self.game = game
        self.end_game = False
        
        # queue of objects that need to be created or destroyed
        self.inbox = []
        self.trash = []
        # attrs ::fix these -- are they all needed? they should be
        #       defined somewhere else::
        # defaults for customizable values

        # is maximum_shots
        #world_diagonal = constants.WORLDSIZE * math.sqrt(2.0)
        #max_bullet_life = constants.WORLDSIZE / constants.SHOTSPEED
        #self.maximum_shots = int(max_bullet_life / constants.RELOADTIME)
        self.timespent = 0.0
        ## these should be set elsewhere
        self.inertia_linear = 1
        self.inertia_angular = 1
        self.taunt_timer = 0
        # self.display = modpygame.Display(self)
        self.taunt_msg = None
        self.taunt_color = None

        # track objects on map
        self.obstacles = [Box(item) for item in config.world.boxes]
        self.build_truegrid()
        self.bases = dict((item.color, Base(item))
                           for item in config.world.bases)

        self.teams = {}
        for color,base in self.bases.items():
            self.teams[color] = Team(self, color, base)

    def update(self, dt):
        """Update the teams."""
        self.timespent += dt
        if self.taunt_msg:
            self.taunt_timer -= dt
            if self.taunt_timer <= 0:
                self.taunt_msg = None
                self.game.display.taunt.update()
                self.game.display.redraw()
        if self.timespent > config['time_limit']:
            self.end_game = True
            return
        for team in self.teams.values():
            team.update(dt)

    def build_truegrid(self):
        self.occgrid = numpy.zeros((config.world.width, config.world.height))
        offset_x = config.world.width/2
        offset_y = config.world.height/2
        for obstacle in self.obstacles:
            if obstacle.rot == 0:
                lx = (obstacle.pos[0] - obstacle.size[0]/2,
                        obstacle.pos[1] - obstacle.size[1]/2)
                for x in xrange(obstacle.size[0]):
                    for y in xrange(obstacle.size[1]):
                        self.occgrid[x+lx[0]+offset_x][y+lx[1]+offset_y] = 1
            else:
                # We didn't have enough time to implement occupancy grids with
                # rotated obstalces; we figured it was low priority anyway
                # because it would be really difficult for students to deal
                # with.  If someone implements it sometime, great.  Until then,
                # this is our workaround - the server returns a fail on a
                # request for the occupancy grid if there are rotated
                # obstacles.
                self.occgrid = None
                break

    def obstacle_at(self, x, y):
        for obstacle in self.obstacles:
            if obstacle.rot == 0:
                if collide.rect2point(obstacle.rect, (x, y)):
                    return True
            else:
                if collide.poly2point(obstacle.shape, (x, y)):
                    return True
        return False

    def tanks(self):
        """Iterate through all tanks on the map."""
        for team in self.teams.values():
            for tank in team.tanks:
                yield tank

    def shots(self):
        """Iterate through all shots on the map."""
        for tank in self.tanks():
            for shot in tank.shots:
                yield shot

    def dropFlag(self, flag):
        if flag.tank is not None:
            flag.tank.flag = None
        flag.tank = None

    def returnFlag(self, flag):
        if flag.tank is not None:
            flag.tank.flag = None
        flag.tank = None
        flag.pos = flag.team.base.pos

    def scoreFlag(self, flag):
        flag.tank.team.score.gotFlag()
        flag.team.score.lostFlag()
        self.returnFlag(flag)

    def closest_base(self, pos):
        items = tuple(sorted((collide.dist(pos, base.center), base)
                      for base in self.bases.values()))
        if abs(items[0][0] - items[1][0]) < 50:
            return None
        return items[0][1]

    def taunt(self, message, color):
        if self.taunt_msg is None:
            self.taunt_msg = message
            self.taunt_timer = 3
            self.taunt_color = color
            return True
        return False


class Team(object):
    """Team object:
    
    Manages a BZRFlag team -- w/ a base, a flag, a score, and tanks.
    
    """
    
    def __init__(self, map, color, base):
        self.color = color
        self.map = map
        ntanks = config[self.color+'_tanks']
        if ntanks is None:
            ntanks = config['default_tanks']

        self.tanks = [SeppiTank(self, i) for i in xrange(ntanks)]
        self.tanks_radius = constants.TANKRADIUS * ntanks * 3/2.0
        self.base = base
        base.team = self
        self.flag = Flag(self)

        self.posnoise = config[self.color+'_posnoise']
        if self.posnoise is None:
            self.posnoise = config['default_posnoise']

        self.angnoise = config[self.color+'_angnoise']
        if self.angnoise is None:
            self.angnoise = config['default_angnoise']

        self.velnoise = config[self.color+'_velnoise']
        if self.velnoise is None:
            self.velnoise = config['default_velnoise']

        self.score = Score(self)
        self._obstacles = []
        self.setup()
        for item in self.tanks+[self.base, self.flag, self.score]:
            self.map.inbox.append(item)

    def setup(self):
        """Initialize the cache of obstacles near the base."""
        self._obstacles = []
        for o in self.map.obstacles:
            if collide.circle2circle((o.center,o.radius),\
            (self.base.center, self.tanks_radius + constants.TANKRADIUS)):
                self._obstacles.append(o)

    def respawn(self, tank, first=True):
        """Respawn a dead tank."""
        tank.status = constants.TANKALIVE
        tank.reset_speed()
        if tank.pos != constants.DEADZONE:
            return
        if not config['freeze_tag']:
            tank.rot = random.uniform(0, 2*math.pi)
        pos = self.spawn_position()
        for i in xrange(constants.RESPAWNTRIES):
            if self.check_position(pos, constants.TANKRADIUS):
                break
            pos = self.spawn_position()
        else:
            raise Exception("No workable spawning spots found for team %s"
                            %self.color)
        tank.pos = pos

    def check_position(self, point, radius):
        """Check a position to see if it is safe to spawn a tank there."""
        for o in self._obstacles:
            if collide.poly2circle(o.shape, (point, radius)):
                return False
        for shot in self.map.shots():
            if collide.circle2circle((point, radius),
                    (shot.pos, constants.SHOTRADIUS)):
                return False
        for tank in self.map.tanks():
            if collide.circle2circle((point, radius),
                    (tank.pos, constants.TANKRADIUS)):
                return False
        if config['freeze_tag']:
            if collide.dist(point, self.base.center) < self.base.radius:
                return False
        if point[0]-radius<-config.world.size[0]/2 or\
           point[1]-radius<-config.world.size[1]/2 or\
           point[0]+radius>config.world.size[0]/2 or\
           point[1]+radius>config.world.size[1]/2:
            return False
        return True

    def spawn_position(self):
        """Generate a random spawning position around the base."""
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0,1) * self.tanks_radius
        return [self.base.center[0] + dist*math.cos(angle),
                self.base.center[1] + dist*math.sin(angle)]

    def update(self, dt):
        """Update the tanks and flag."""
        for tank in self.tanks:
            tank.update(dt)
        self.flag.update(dt)
        self.score.update(dt)

    def tank(self, id):
        """Get a tank based on its ID."""
        if 0<=id<len(self.tanks):
            return self.tanks[id]
        raise ValueError("Invalid tank ID: %s"%id)

    def shoot(self, tankid):
        """Tell a tank to shoot."""
        return self.tank(tankid).shoot()

    def speed(self, tankid, value):
        """Set a tank's goal speed."""
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        if not (1 >= value >= -1):
            raise Exception("not a number")
        self.tank(tankid).setspeed(value)

    def angvel(self, tankid, value):
        """Set a tank's goal angular velocity."""
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        if not (1 >= value >= -1):
            raise Exception("not a number")
        self.tank(tankid).setangvel(value)


class Tank(object):
    """BZFlag Tank
    
    Handles the logic for dealing with a tank in the game.

    Attributes:
        rot: angular rotation in radians; always between 0 and 2*pi
        
    """
    size = (constants.TANKRADIUS*2,) * 2
    radius = constants.TANKRADIUS

    def __init__(self, team, tankid):
        self.team = team
        self.pos = constants.DEADZONE
        self.rot = 0
        self.angvel = 0
        self.callsign = self.team.color + str(tankid)
        self.status = constants.TANKDEAD
        self.shots = []
        self.reloadtimer = 0
        self.dead_timer = -1
        self.flag = None
        self.spawned = False

    def reset_speed(self):
        raise NotImplementedError

    def setspeed(self, speed):
        raise NotImplementedError

    def setangvel(self, angvel):
        raise NotImplementedError

    def setaccelx(self, value):
        raise NotImplementedError

    def setaccely(self, value):
        raise NotImplementedError

    def shoot(self):
        raise NotImplementedError

    def kill(self):
        """Destroy the tank."""
        self.status = constants.TANKDEAD
        self.dead_timer = config['respawn_time']
        self.team.score.score_tank(self)
        if self.flag:
            self.team.map.dropFlag(self.flag)
            self.flag = None
        for shot in self.shots:
            shot.kill()
        self.shots = []

    def collision_at(self, pos):
        for obs in self.team.map.obstacles:
            if collide.poly2circle(obs.shape, ((pos),constants.TANKRADIUS)):
                return True
        for tank in self.team.map.tanks():
            if tank is self:continue
            if collide.circle2circle((tank.pos, constants.TANKRADIUS),
                                     (pos, constants.TANKRADIUS)):
                self.collide_tank(tank)
                return True
        radius = constants.TANKRADIUS
        if pos[0]-radius<-config.world.size[0]/2 or\
         pos[1]-radius<-config.world.size[1]/2 or\
         pos[0]+radius>config.world.size[0]/2 or \
         pos[1]+radius>config.world.size[1]/2:
            return True
        return False

    def collide_tank(self, tank):
        pass

    def update(self, dt):
        """Update the tank's position, status, velocities."""
        if (self.pos == constants.DEADZONE and
                self.status != constants.TANKDEAD):
            self.team.respawn(self)
        if self.status == constants.TANKDEAD:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.team.respawn(self,not self.spawned)
                self.spawned = True
            return

        self.update_goals(dt)
        dx,dy = self.velocity()
        if not self.collision_at((self.pos[0]+dx*dt, self.pos[1]+dy*dt)):
            self.pos[0] += dx*dt
            self.pos[1] += dy*dt
        elif not self.collision_at((self.pos[0], self.pos[1]+dy*dt)):
            self.pos[1] += dy*dt
        elif not self.collision_at((self.pos[0]+dx*dt, self.pos[1])):
            self.pos[0] += dx*dt

    def update_goal(self, num, goal, by):
        if num < goal:
            num += by
            if num > goal:
                return goal
            return num
        elif num > goal:
            num -= by
            if num < goal:
                return goal
            return num
        else:
            return num

    def update_goals(self, dt):
        raise NotImplementedError

    def velocity(self):
        raise NotImplementedError


class SeppiTank(Tank):

    def __init__(self, team, tankid):
        super(SeppiTank, self).__init__(team, tankid)
        self.goal_speed = 0
        self.goal_angvel = 0
        self.speed = 0
        self.angvel = 0
        self.rot = 0

    def update(self, dt):
        """Update tank's position, status, etc."""
        for shot in self.shots:
            shot.update(dt)
        if self.reloadtimer > 0:
            self.reloadtimer -= dt
        super(SeppiTank, self).update(dt)

    def update_goals(self, dt):
        """Update the velocities to match the goals."""
        self.speed = self.update_goal(self.speed, self.goal_speed,
                                      constants.LINEARACCEL * dt)
        self.angvel = self.update_goal(self.angvel, self.goal_angvel,
                                       constants.ANGULARACCEL * dt)
        self.rot += self.angvel * constants.TANKANGVEL * dt
        # Normalize the angle to be between 0 and 2*pi
        self.rot = self.rot % (2 * math.pi)

    def reset_speed(self):
        self.goal_speed = 0
        self.goal_angvel = 0
        self.speed = 0
        self.angvel = 0
        self.rot = 0

    def setspeed(self, speed):
        """Set the goal speed."""
        self.goal_speed = speed

    def setangvel(self, angvel):
        """Set the goal angular velocity."""
        self.goal_angvel = angvel

    def shoot(self):
        """Tell the tank to shoot."""
        if self.reloadtimer > 0 or \
                len(self.shots) >= config['max_shots']:
            return False
        shot = Shot(self)
        self.shots.insert(0, shot)
        self.team.map.inbox.append(shot)
        self.reloadtimer = constants.RELOADTIME
        return True

    def kill(self):
        super(SeppiTank, self).kill()
        self.pos = constants.DEADZONE

    def velocity(self):
        """Calculate the tank's linear velocity."""
        return (self.speed * math.cos(self.rot) * constants.TANKSPEED,
            self.speed * math.sin(self.rot) * constants.TANKSPEED)


class Shot(object):
    size = (constants.SHOTRADIUS*2,) * 2
    """Shot object:
    
    Contains the logic for a shot on the map.
    
    """
    
    def __init__(self, tank):
        self.tank = tank
        self.team = tank.team
        self.rot = self.tank.rot
        self.distance = 0
        self.pos = tank.pos[:]
        speed = constants.SHOTSPEED + tank.speed
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))
        self.status = constants.SHOTALIVE

    def update(self, dt):
        """Move the shot."""
        if (self.status == constants.SHOTDEAD or
            self.pos == constants.DEADZONE):
            return
        self.distance += math.hypot(self.vel[0]*dt, self.vel[1]*dt)

        ## do we need to lerp?
        if self.vel[0]*dt > constants.TANKRADIUS*2 or \
            self.vel[0]*dt > constants.TANKRADIUS*2:
                p1 = self.pos[:]
                p2 = [self.pos[0]+self.vel[0]*dt, \
                    self.pos[1]+self.vel[1]*dt]
                self.check_line(p1,p2)
        else:
            self.pos[0] += self.vel[0]*dt
            self.pos[1] += self.vel[1]*dt
            self.check_collisions()
        if self.distance > constants.SHOTRANGE:
            self.kill()

    def check_collisions(self):
        for obs in self.team.map.obstacles:
            if collide.poly2circle(obs.shape, 
                                  ((self.pos),constants.SHOTRADIUS)):
                return self.kill()
        for tank in self.team.map.tanks():
            if self in tank.shots:continue
            if collide.circle2circle((tank.pos, constants.TANKRADIUS),
                                     (self.pos, constants.SHOTRADIUS)):
                if tank.team == self.team and not config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        if self.pos[0]<-config.world.size[0]/2 or\
         self.pos[1]<-config.world.size[1]/2 or\
         self.pos[0]>config.world.size[0]/2 or \
         self.pos[1]>config.world.size[1]/2:
            return self.kill()

    def check_line(self, p1, p2):
        for obs in self.team.map.obstacles:
            if collide.rect2line(obs.rect, (p1,p2)):
                return self.kill()
        for tank in self.team.map.tanks():
            if collide.circle2line((tank.pos,constants.TANKRADIUS + 
                                    constants.SHOTRADIUS), (p1,p2)):
                if tank.team == self.team and not config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        if self.pos[0]<-config.world.size[0]/2 or\
           self.pos[1]<-config.world.size[1]/2 or\
           self.pos[0]>config.world.size[0]/2 or \
           self.pos[1]>config.world.size[1]/2:
            return self.kill()

    def kill(self):
        """Remove the shot from the map."""
        self.status = constants.SHOTDEAD
        self.tank.team.map.trash.append(self)
        if self in self.tank.shots:
            self.tank.shots.remove(self)


class Flag(object):
    """Flag object:
    
    Contains the logic for team flags on a map.
    
    """
    
    size = (constants.FLAGRADIUS*2,) * 2
    
    def __init__(self, team):
        self.team = team
        self.rot = 0
        self.pos = team.base.center
        self.tank = None

    def update(self, dt):
        """Update the flag's position."""
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos
            if collide.rect2circle(self.tank.team.base.rect,
                                  (self.pos, constants.FLAGRADIUS)):
                self.tank.team.map.scoreFlag(self)
        else:
            # handle collide
            for tank in self.team.map.tanks():
                if collide.circle2circle((self.pos, constants.FLAGRADIUS),
                                         (tank.pos, constants.TANKRADIUS)):
                    if tank.team is self.team:
                        self.team.map.returnFlag(self)
                    else:
                        self.tank = tank
                        tank.flag = self
                    return


def rotate_scale(p1, p2, angle, scale = 1.0):
    """Rotate p1 around p2 with an angle of angle."""
    theta = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
    dst = math.hypot(p1[0]-p2[0], p1[1]-p2[1]) * scale
    return (p2[0] + dst*math.cos(theta + angle),
        p2[1] + dst*math.sin(theta + angle))


def convertBoxtoPoly(center, size, rotation = 0):
    """Convert a box to a polygon (list of points)."""
    d = (1,1),(1,-1),(-1,-1),(-1,1)
    x,y = center
    w,h = size
    for dx,dy in d:
        yield x + w/2*dx, y + h/2 * dy


def scale_rotate_poly(points, scale, rotation):
    points = list(points)
    center = polygon_center(points)
    for point in points:
        yield rotate_scale(point, center, rotation, scale)


def polygon_center(points):
    points = tuple(points)
    cx = sum(p[0] for p in points)/len(points)
    cy = sum(p[1] for p in points)/len(points)
    return cx,cy


class Base(object):
    """Base object:
    
    Contains the logic & data for a team's Base on a map.
    
    """
    
    def __init__(self, item):
        self.color = item.color
        self.center = self.pos = item.pos.asList()
        self.size = tuple(x*2 for x in item.size.asList())
        self.radius = math.sqrt((self.size[0]/2)**2 + (self.size[1]/2)**2)
        poly = tuple(convertBoxtoPoly(item.pos,self.size))
        self.rect = (item.pos[0]-self.size[0]/2, 
                     item.pos[1]-self.size[1]/2) + self.size
        self.shape = list(scale_rotate_poly(poly, 1, item.rot))
        self.rot = item.rot


class Obstacle(object):
    """Obstacle object:
    
    Contains the logic and data for an obstacle on the map.
    
    """
    
    def __init__(self, item):
        self.center = self.pos = item.pos.asList()
        self.shape = ()
        self.rot = item.rot
        self.radius = 0

    def pad(self, padding):
        self.shape = list(scale_rotate_poly(self.shape, 
                         (self.radius + padding)/float(self.radius), 0))


class Box(Obstacle):
    """A Box Obstacle."""
    
    def __init__(self, item):
        Obstacle.__init__(self, item)
        self.radius = math.hypot(*item.size)
        self.size = tuple(x*2 for x in item.size.asList())
        self.shape = list(scale_rotate_poly((convertBoxtoPoly
                         (item.pos, self.size,item.rot)), 1, item.rot))
        self.rect = (tuple(self.pos)+self.size)


class Score(object):
    """Score object: keeps track of a team's score."""
    
    def __init__(self, team):
        self.team = team
        self.value = 0
        self.flags = 0
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer > 2:
            self.timer = 0
            for tank in self.team.tanks:
                self.score_tank(tank)

    def score_tank(self, tank):
        if tank.flag:
            ebase = tank.flag.team.base
            distance_to = collide.dist(self.team.base.center, 
                                       tank.flag.team.base.center)
            distance_back = collide.dist(tank.pos,self.team.base.center)
            more = 100.0 * (distance_to - distance_back)/distance_to
            if distance_back > distance_to:
                more = 0
            self.setValue(500 + more)
        else:
            closest = None
            for color,team in self.team.map.teams.items():
                if team is self.team:continue
                dst = collide.dist(tank.pos, team.base.center)
                if closest is None or dst < closest[0]:
                    closest = dst, team.base
            if not closest:
                logger.warning("no closest found... %s" % self.team.color)
                return False
            total_dist = collide.dist(self.team.base.center,closest[1].center)
            distance_to = collide.dist(tank.pos, closest[1].center)
            if distance_to > total_dist:return
            self.setValue(100.0 * (total_dist-distance_to)/total_dist)

    def gotFlag(self):
        self.value = 0
        self.flags += 1

    def lostFlag(self):
        self.flags -= 1

    def setValue(self,value):
        if value>self.value:
            self.value = value

    def text(self):
        return "Team %s: %d"%(self.team.color, self.total())

    def total(self):
        return 1000*self.flags + self.value


