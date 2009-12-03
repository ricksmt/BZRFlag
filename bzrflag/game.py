import collide
import math

class Game:
    def __init__(self, config, displayclass, inputclass):
        self.map = Map(self, config)
        self.display = displayclass(self)
        self.input = inputclass(self)
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
        while self.running:
            if self.map.end_game:
                # do something else here?
                break
            self.input.update()
            self.update()
            self.update_sprites()
            self.display.update()

class Map(object):
    """manages the map data. takes a config object and populates
    the current map with bases, obstacles, teams and tanks."""
    def __init__(self, game, config):
        self.game = game
        # track objects on map
        self.obstacles = [Obstacle(item) for item in config.world.boxes]
        self.bases = dict((item.color, Base(item)) for item in config.world.bases)

        self.teams = {}
        for color,base in self.bases.items():
            self.teams[color] = Team(self, color, base, config)
            self.spawn_flag(color)

        # defaults for customizable values
        world_diagonal = constants.WORLDSIZE * math.sqrt(2.0)
        max_bullet_life = constants.WORLDSIZE / constants.SHOTSPEED
        self.maximum_shots = int(max_bullet_life / constants.RELOADTIME)
        self.timespent = 0.0
        self.timelimit = 300000.0
        self.inertia_linear = 1
        self.inertia_angular = 1
        self.tank_angvel = constants.TANKANGVEL
        ## why is max_tanks important?
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

    def update(self, dt):
        self.timespent += dt
        if self.timespent > self.timelimit:
            self.end_game = True
            return
        for team in self.teams:
            team.update(dt)

    def handle_collisions(self, dt):
        """Handles the collision detecting process for a given object.

        The obj parameter is the object, while the dt is the time elapsed
        since collisions were last handled for this object. As a result of
        calling this method, the object's new position and status (alive,
        dead, etc.) are set.
        """

'''
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
'''

'''pretty well done'''
class Team(object):
    def __init__(self, map, color, base, config):
        self.color = color
        self.map = map
        self.tanks = [Tank(self, i) for i in xrange(int(config.get(self.color+'_tanks',10)))]
        self.tanks_radius = constants.TANKRADIUS * len(self.tanks) * 5
        self.base = base
        self.flag = Flag(self)
        # get rid of?
        self.captured_flags = []
        ## what's with the noise?
        self.posnoise = config.get(self.color+'_posnoise',0)
        self.angnoise = config.get(self.color+'_angnoise',0)
        self.velnoise = config.get(self.color+'_velnoise',0)
        self.score = Score(self)
        self._obstacles = []

    def setup(self):
        self._obstacles = []
        for o in self.map.obstacles:
            if collide.circle2circle((o.center,o.radius),\
            (self.base.center, self.tanks_radius + constants.TANKRADIUS)):
                self._obstacles.append(o)

    def respawn(self, tank):
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
        for o in self._obstacles:
            if collide.poly2circle(o.shape, (point, radius)):
                return False
        for shot in self.map.shots():
            if collide.circle2circle((point, radius),
                    (shot.center, shot.radius)):
                return False
        for tank in self.map.tanks():
            if collide.circle2circle((point, radius),
                    (tank.pos, constants.TANKRADIUS)):
                return False
        return True

    def spawn_position(self):
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0,1) * self.tanks_radius
        return self.base.pos[0] + dist*math.cos(angle), self.base.pos[1] + dist*math.sin(angle)

    def update(self, dt):
        for tank in self.tanks:
            tank.update(dt)
        self.flag.update(dt)

    def tank(self, id):
        if 0<=id<len(self.tanks):
            return self.tanks[id]
        raise Exception,"Invalid tank ID: %s"%id

    def shoot(self, tankid):
        return self.tank(tankid).shoot()

    def speed(self, tankid, value):
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tank(tankid).speed(value)

    def angvel(self, tankid, value):
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        self.tank(tankid).angvel(value)

## TODO: i don't like constants. especially ALL_CAPS

class Tank(object):
    size = (constants.TANKRADIUS,) * 2
## internally complete
    def __init__(self, team, tankid):
        self.team = team
        self.pos = [0,0]
        self.rot = 0
        self.speed = 0
        self.vel = (0, 0)
        self.angvel = 0
        self.goal_speed = 0
        self.goal_angvel = 0
        self.callsign = self.team.color + str(tankid)
        self.status = constants.TANKDEAD
        self.shots = []
        self.reloadtimer = 0
        self.flag = None
        self.dead_timer = -1

    def speed(self, speed):
        self.goal_speed = speed

    def angvel(self, angvel):
        self.goal_angvel = angvel

    def shoot(self):
        if self.reloadtimer > 0 or \
                len(self.shots) == self.team.map.maximum_shots:
            return False
        self.shots.insert(0, Shot(self))
        self.reloadtimer = constants.RELOADTIME

    def kill(self):
        self.team.map.trash.append(self)
        self.status = constants.TANKDEAD
        self.dead_timer = self.team.map.respawn_time
        if self.flag:
            self.team.map.returnFlag(self.flag)
            self.flag = None

    def update(self, dt):
        if self.status == constants.TANKDEAD:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.team.respawn(self)
            return

        for shot in self.shots:
            shot.update(dt)

        if self.reloadtimer > 0:
            self.reloadtimer -= dt

        self.update_goals()
        self.rot += self.angvel
        dx,dy = self.velocity()
        self.pos[0] += dx
        self.pos[1] += dy

    def update_goals(self):
        if self.speed < self.goal_speed:
            self.speed += constants.LINEARACCEL * dt
            if self.speed > self.goal_speed:
                self.speed = sefl.goal_speed
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
        return (self.speed * math.cos(self.rot) * constants.TANKSPEED,
            self.speed * math.sin(self.rot) * constants.TANKSPEED)

class Shot(object):
    size = (constants.SHOTRADIUS,) * 2

    def __init__(self, tank):
        self.tank = tank
        self.color = self.tank.team.color
        self.rot = self.tank.rot
        self.distance = 0
        self.pos = tank.pos

        speed = constants.SHOTSPEED + tank.speed
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))

        self.status = constants.SHOTALIVE

    def update(self, mapper, dt):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        if self.distance > constants.SHOTRANGE:
            self.status = constants.SHOTDEAD
        if self.status == constants.SHOTDEAD:
            mapper.trash.append(self)
            self.tank.shots.remove(self)
            for team in mapper.teams:
                if team.color == self.color:
                    team.shots.remove(self)
        # handle collide


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
        # handle collide

def rotate_around(p1, p2, angle):
    '''rotate p1 around p2'''
    theta = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
    dst = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
    return (p2[0] + dst*math.cos(theta + angle),
        p2[1] + dst*math.sin(theta + angle))

class Base(object):
    def __init__(self, item):
        self.color = item.color
        self.center = item.pos.asList()
        self.size = item.size.asList()
        self.radius = math.sqrt(self.size[0]**2 + self.size[1]**2)
        self.shape = tuple(self.lst_corners(item))

    def lst_corners(self, item):
        d = (1,1),(1,-1),(-1,-1),(-1,1)
        w,h = self.size
        x,y = self.center
        for dx,dy in d:
            point = x + w/2*dx, y + h/2 * dy
            yield rotate_around(point, self.center, item.rot)


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
