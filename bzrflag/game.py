import collide
import math
import random
import datetime

import constants
import config

class Game:
    """*Main control object. Contains the main loop.*

    Attributes:

    * map => :class:`game.Map`
    * input => :class:`headless.Input`
    * display => :class:`modpygame.Display`
    """
    def __init__(self):

        import headless
        import modpygame

        self.display = modpygame.Display(self)
        self.map = Map(self)
        self.input = headless.Input(self)
        
        self.running = False
        self.gameover = False
        self.timestamp = datetime.datetime.utcnow()

    def update(self):
        """updates the game world"""

        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now

        dt = ((24 * 60 * 60) * delta.days
                + delta.seconds
                + (10 ** -6) * delta.microseconds)

        self.map.update(dt)

    def update_sprites(self):
        """adds and removes sprites from the display"""
        while len(self.map.inbox) > 0:
            self.display.add_object(self.map.inbox.pop())
        while len(self.map.trash) > 0:
            self.display.remove_object(self.map.trash.pop())

    def loop(self):
        """the main loop of bzflag. checks events, updates positions,
        and draws to the screen until the pygame window is closed."""
        self.running = True
        self.display.setup()
        while self.running:
            if self.map.end_game:
                # do something else here?
                break
            self.input.update()
            self.update()
            self.update_sprites()
            self.display.update()

class Map(object):
    """manages the map data. populates
    the current map with bases, obstacles, teams and tanks."""
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

        # track objects on map
        self.obstacles = [Box(item) for item in config.config.world.boxes]
        self.bases = dict((item.color, Base(item)) for item in config.config.world.bases)

        self.teams = {}
        for color,base in self.bases.items():
            self.teams[color] = Team(self, color, base)

    def update(self, dt):
        '''update the teams'''
        self.timespent += dt
        if self.timespent > config.config['time_limit']:
            self.end_game = True
            return
        for team in self.teams.values():
            team.update(dt)
        self.handle_collisions(dt)

    def tanks(self):
        '''iterate through all tanks on the map'''
        for team in self.teams.values():
            for tank in team.tanks:
                yield tank

    def shots(self):
        '''iterate through all shots on the map'''
        for tank in self.tanks():
            for shot in tank.shots:
                yield shot

    def handle_collisions(self, dt):
        """Handles the collision detecting process for a given object.

        The obj parameter is the object, while the dt is the time elapsed
        since collisions were last handled for this object. As a result of
        calling this method, the object's new position and status (alive,
        dead, etc.) are set.
        """
        collides = {}



class Team(object):
    '''Team object:
    manages a BZRFlag team -- w/ a base, a flag, a score, and tanks.'''
    def __init__(self, map, color, base):
        self.color = color
        self.map = map
        self.tanks = [Tank(self, i) for i in xrange(config.config[self.color+'_tanks'])]
        self.tanks_radius = constants.TANKRADIUS * len(self.tanks) * 3/2.0
        self.base = base
        base.team = self
        self.flag = Flag(self)
        # get rid of?
        self.captured_flags = []
        self.posnoise = config.config[self.color+'_posnoise']
        self.angnoise = config.config[self.color+'_angnoise']
        self.velnoise = config.config[self.color+'_velnoise']
        self.score = Score(self)
        self._obstacles = []
        self.map.inbox.append(self.base)
        for tank in self.tanks:
            self.map.inbox.append(tank)

    def setup(self):
        '''initialize the cache of obstacles near the base'''
        self._obstacles = []
        for o in self.map.obstacles:
            if collide.circle2circle((o.center,o.radius),\
            (self.base.center, self.tanks_radius + constants.TANKRADIUS)):
                self._obstacles.append(o)

    def respawn(self, tank):
        '''respawn a dead tank'''
        pos = self.spawn_position()
        for i in xrange(1000):
            if self.check_position(pos, constants.TANKRADIUS):
                break
            pos = self.spawn_position()
        else:
            raise Exception,"No workable spawning spots found for team %s"%self.color
        tank.status = constants.TANKALIVE
        tank.pos = pos
        tank.rot = random.uniform(0, 2*math.pi)

    def check_position(self, point, radius):
        '''check a position to see if it is safe to spawn a tank there'''
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
        return True

    def spawn_position(self):
        '''generate a random spawning position around the base'''
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0,1) * self.tanks_radius
        return [self.base.center[0] + dist*math.cos(angle), self.base.center[1] + dist*math.sin(angle)]

    def update(self, dt):
        '''update the tanks and flag'''
        for tank in self.tanks:
            tank.update(dt)
        self.flag.update(dt)

    def tank(self, id):
        '''get a tank based on its ID'''
        if 0<=id<len(self.tanks):
            return self.tanks[id]
        raise Exception,"Invalid tank ID: %s"%id

    def shoot(self, tankid):
        '''tell a tank to shoot'''
        return self.tank(tankid).shoot()

    def speed(self, tankid, value):
        '''set a tank's goal speed'''
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tank(tankid).setspeed(value)

    def angvel(self, tankid, value):
        '''set a tank's goal angular velocity'''
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tank(tankid).setangvel(value)

class Tank(object):
    size = (constants.TANKRADIUS*2,) * 2
    radius = constants.TANKRADIUS
## internally complete
    '''Tank object:
    handles the logic for dealing with a tank in the game'''
    def __init__(self, team, tankid):
        self.team = team
        self.pos = [0,0]
        self.rot = 0
        self.speed = 0
        self.angvel = 0
        self.goal_speed = 0
        self.goal_angvel = 0
        self.callsign = self.team.color + str(tankid)
        self.status = constants.TANKDEAD
        self.shots = []
        self.reloadtimer = 0
        self.dead_timer = -1
        self.flag = None

    def setspeed(self, speed):
        '''set the goal speed'''
        self.goal_speed = speed

    def setangvel(self, angvel):
        '''set the goal angular velocity'''
        self.goal_angvel = angvel

    def shoot(self):
        '''tell the tank to shoot'''
        if self.reloadtimer > 0 or \
                len(self.shots) >= config.config['max_shots']:
            return False
        shot = Shot(self)
        self.shots.insert(0, shot)
        self.team.map.inbox.append(shot)
        self.reloadtimer = constants.RELOADTIME

    def kill(self):
        '''destroy the tank'''
        self.status = constants.TANKDEAD
        self.dead_timer = config.config['respawn_time']
        self.team.score.tank_died(self)
        self.pos = constants.DEADZONE
        if self.flag:
            self.team.map.returnFlag(self.flag)
            self.flag = None

    def collision_at(self, pos):
        #return False
        for obs in self.team.map.obstacles:
            if collide.rect2circle(obs.rect, ((pos),constants.TANKRADIUS)):
                return True
        for tank in self.team.map.tanks():
            if tank is self:continue
            if collide.circle2circle((tank.pos, constants.TANKRADIUS),
                                     (pos, constants.TANKRADIUS)):
                return True
        if pos[0]<-config.config.world.size[0]/2 or\
         pos[1]<-config.config.world.size[1]/2 or\
         pos[0]>config.config.world.size[0]/2 or \
         pos[1]>config.config.world.size[1]/2:
            return True
        return False

    def update(self, dt):
        '''update the tank's position, status, velocities'''
        if self.status == constants.TANKDEAD:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.team.respawn(self)
            return

        for shot in self.shots:
            shot.update(dt)

        if self.reloadtimer > 0:
            self.reloadtimer -= dt

        self.update_goals(dt)
        self.rot += self.angvel * constants.TANKANGVEL * dt
        dx,dy = self.velocity()
        if not self.collision_at((self.pos[0]+dx*dt, self.pos[1]+dy*dt)):
            self.pos[0] += dx*dt
            self.pos[1] += dy*dt

    def update_goals(self, dt):
        '''update the velocities to match the goals'''
        if self.speed < self.goal_speed:
            self.speed += constants.LINEARACCEL * dt
            if self.speed > self.goal_speed:
                self.speed = self.goal_speed
        elif self.speed > self.goal_speed:
            self.speed -= constants.LINEARACCEL * dt
            if self.speed < self.goal_speed:
                self.speed = self.goal_speed

        if self.angvel < self.goal_angvel:
            self.angvel += constants.ANGULARACCEL * dt
            if self.angvel > self.goal_angvel:
                self.angvel = self.goal_angvel
        elif self.angvel > self.goal_angvel:
            self.angvel -= constants.ANGULARACCEL * dt
            if self.angvel < self.goal_angvel:
                self.angvel = self.goal_angvel

    def velocity(self):
        '''calculate the tank's linear velocity'''
        return (self.speed * math.cos(self.rot) * constants.TANKSPEED,
            self.speed * math.sin(self.rot) * constants.TANKSPEED)

class Shot(object):
    size = (constants.SHOTRADIUS*2,) * 2
    '''Shot object:
    contains the logic for a shot on the map'''
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
        '''move the shot'''
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
        # handle collide

    def check_collisions(self):
        for obs in self.team.map.obstacles:
            if collide.rect2circle(obs.rect, ((self.pos),constants.SHOTRADIUS)):
                return self.kill()
        for tank in self.team.map.tanks():
            if collide.circle2circle((tank.pos, constants.TANKRADIUS),
                                     (self.pos, constants.SHOTRADIUS)):
                if tank.team == self.team and not config.config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        if self.pos[0]<-config.config.world.size[0]/2 or\
         self.pos[1]<-config.config.world.size[1]/2 or\
         self.pos[0]>config.config.world.size[0]/2 or \
         self.pos[1]>config.config.world.size[1]/2:
            return self.kill()

    def check_line(self, p1, p2):
        for obs in self.team.map.obstacles:
            if collide.rect2line(obs.rect, (p1,p2)):
                return self.kill()
        for tank in self.team.map.tanks():
            if collide.circle2line((tank.pos, constants.TANKRADIUS + constants.SHOTRADIUS),
                                     (p1,p2)):
                if tank.team == self.team and not config.config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        if self.pos[0]<-config.config.world.size[0]/2 or\
         self.pos[1]<-config.config.world.size[1]/2 or\
         self.pos[0]>config.config.world.size[0]/2 or \
         self.pos[1]>config.config.world.size[1]/2:
            return self.kill()

    def kill(self):
        '''remove the shot from the map'''
        self.status = constants.SHOTDEAD
        self.tank.team.map.trash.append(self)
        if self in self.tank.shots:
            self.tank.shots.remove(self)

class Flag(object):
    size = (constants.FLAGRADIUS*2,) * 2
    '''Flag object:
    contains the logic for team flags on a map'''
    def __init__(self, team):
        self.team = team
        self.rot = 0
        self.pos = team.base.center
        self.tank = None
        #if tank is not None:
        #    self.tank = tank

    def update(self, dt):
        '''update the flag's position'''
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos
        # handle collide

def rotate_scale(p1, p2, angle, scale = 1.0):
    '''rotate p1 around p2 with an angle of angle'''
    theta = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
    dst = math.hypot(p1[0]-p2[0], p1[1]-p2[1]) * scale
    return (p2[0] + dst*math.cos(theta + angle),
        p2[1] + dst*math.sin(theta + angle))

def convertBoxtoPoly(center, size, rotation = 0):
    '''convert a box to a polygon (list of points)'''
    d = (1,1),(1,-1),(-1,-1),(-1,1)
    x,y = center
    w,h = size
    for dx,dy in d:
        yield x + w/2*dx, y + h/2 * dy

def scale_rotate_poly(points, scale, rotation):
    center = polygon_center(points)
    for point in points:
        yield rotate_scale(point, (cx,cy), rotation, scale)

def polygon_center(points):
    points = tuple(points)
    cx = sum(p[0] for p in points)/len(points)
    cy = sum(p[1] for p in points)/len(points)
    return cx,cy

class Base(object):
    '''Base object:
    contains the logic & data for a team's Base on a map'''
    def __init__(self, item):
        self.color = item.color
        self.center = self.pos = item.pos.asList()
        self.size = tuple(x*2 for x in item.size.asList())
        self.radius = math.sqrt((self.size[0]/2)**2 + (self.size[1]/2)**2)
        poly = tuple(convertBoxtoPoly(item.pos,item.size))
        self.shape = scale_rotate_poly(poly, 1, item.rot)
        self.rot = item.rot

class Obstacle(object):
    '''Obstacle object:
    contains the logic and data for an obstacle on the map'''
    def __init__(self, item):
        self.center = self.pos = item.pos.asList()
        self.shape = ()
        self.rot = item.rot
        self.radius = 0

    def pad(self, padding):
        self.shape = scale_rotate_poly(self.shape, (self.radius + padding)/float(self.radius), 0)

class Box(Obstacle):
    '''a Box Obstacle'''
    def __init__(self, item):
        Obstacle.__init__(self, item)
        self.radius = math.hypot(*item.size)
        self.shape = scale_rotate_poly((convertBoxtoPoly(item.pos,item.size,item.rot)), 1, item.rot)
        self.size = item.size
        self.rect = (item.pos.asList()+item.size.asList())

class Score(object):
    '''Score object: keeps track of a team's score'''
    def __init__(self, team):
        self.team = team
        self.value = 0

    def tank_died(self, tank):
        if tank.flag:
            distance_to = collide.dist(self.team.base.center,tank.flag.team.base.center)
            distance_back = collide.dist(tank.pos,self.team.base.center)
            self.setValue(distance_to + distance_back)
        else:
            closest = None
            for color,team in self.team.map.teams.items():
                if team is self.team:continue
                dst = collide.dist(tank.pos, team.base.center)
                if closest is None or dst < closest[0]:
                    closest = dst, team.base
            if not closest:
                return False
            distance_to = collide.dist(self.team.base.center,closest[1].center)
            self.setValue(distance_to - collide.dist(tank.pos, closest[1].center))

    def setValue(self,value):
        if value>self.value:
            self.value = value

