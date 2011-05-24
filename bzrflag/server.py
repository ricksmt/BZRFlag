"""
The Server object listens on a port for incoming connections.  When a client
connects, the Server dispatches its connection to a new Handler.
"""

import asynchat
import asyncore
import math
import socket
import time
import random
import logging
import numpy
logger = logging.getLogger('server')

import constants
from config import config

BACKLOG = 5


class Server(asyncore.dispatcher):
    """Server that listens on the BZRC port and dispatches connections.

    Each team has its own server which dispatches sessions to the Handler.
    Only one connection is allowed at a time.  Any subsequent connections will
    be rejected until the active connection closes.
    """
    def __init__(self, addr, team):
        self.team = team
        self.in_use = False
        sock = socket.socket()
        asyncore.dispatcher.__init__(self, sock)
        self.sock = sock

        # Disable Nagle's algorithm because this is a latency-sensitive
        # low-bandwidth application.
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.bind(addr)
        self.listen(BACKLOG)
        ## print self.sock,addr

    def handle_accept(self):
        sock, addr = self.accept()
        if self.in_use:
            sock.close()
        else:
            self.in_use = True
            Handler(sock, self.team, self.handle_closed_handler)
            self.sock = sock

    def get_port(self):
        return self.socket.getsockname()[1]

    def handle_closed_handler(self):
        self.in_use = False

    def __del__(self):
        if self.sock:
            self.sock.close()


class Handler(asynchat.async_chat):
    """Handler which implements the BZRC protocol with one client.

    Methods whose names start with "bzrc_" are automagically interpreted as
    bzrc commands.  To create the command "xyz", just create a method called
    "bzrc_xyz", and the Handler will automatically call it when the client
    sends an "xyz" request.  You don't have to add it to a table or anything.
    """
    def __init__(self, sock, team, closed_callback):
        asynchat.async_chat.__init__(self, sock)
        self.team = team
        self.closed_callback = closed_callback
        self.set_terminator('\n')
        self.input_buffer = ''
        self.push('bzrobots 1\n')
        self.init_timestamp = time.time()
        self.established = False

    def handle_close(self):
        self.close()

    def collect_incoming_data(self, chunk):
        if self.input_buffer:
            self.input_buffer += chunk
        else:
            self.input_buffer = chunk

    def push(self, text):
        asynchat.async_chat.push(self, text)
        if config['telnet_console']:
            self.team.map.game.display.console.write(self.team.color + ' > ' + text)
        logger.debug(self.team.color + ' > ' + text)
        if text.startswith('fail '):
            logger.error(self.team.color + ' > ' + text)

    def found_terminator(self):
        """Called when Asynchat finds an end-of-line.

        Note that Asynchat ensures that our input buffer contains everything
        up to but not including the newline character.
        """
        if config['telnet_console']:
            self.team.map.game.display.console.write(self.team.color + ' : ' + self.input_buffer + '\n')
        logger.debug(self.team.color + ' : ' + self.input_buffer + '\n')
        args = self.input_buffer.split()
        self.input_buffer = ''
        if args:
            if self.established:
                try:
                    command = getattr(self, 'bzrc_%s' % args[0])
                except AttributeError:
                    self.push('fail invalid command\n')
                    return
                try:
                    command(args)
                except Exception, e:
                    logger.error(self.team.color + ' : ERROR : %s : %s\n' % (args, e))
                    self.team.map.game.display.console.write(self.team.color + ' : ERROR : %s : %s : %s\n' % (args, e.__class__.__name__, e))
                    self.push('fail %s\n' % e)
                    return
            elif args == ['agent', '1']:
                self.established = True
            else:
                self.bad_handshake()

    def bad_handshake(self):
        """Called when the client gives an invalid handshake message."""
        self.push('fail Unrecognized handshake\n')
        self.close()

    def close(self):
        self.closed_callback()
        asynchat.async_chat.close(self)

    def invalid_args(self, args):
        self.ack(*args)
        self.push('fail Invalid parameter(s)\n')

    def ack(self, *args):
        timestamp = time.time() - self.init_timestamp
        arg_string = ' '.join(str(arg) for arg in args)
        self.push('ack %s %s\n' % (timestamp, arg_string))

    def bzrc_taunt(self, args):
        ## purposely undocumented
        try:
            command = args[0]
            msg = args[1:]
            if not len(msg) or msg[0] != 'please' or msg[-1] != 'thanks':
                raise ValueError
        except ValueError, IndexError:
            self.push('fail invalid command\n')
            return
        self.ack(*args)
        if self.team.map.taunt(' '.join(msg[1:-1]), self.team.color):
            self.push('ok\n')
        else:
            self.push('fail\n')

    def bzrc_help(self, args):
        """help [command]

        If no command is given, list the commands.  Otherwise, return specific
        help for a command.
        """
        if len(args)==1:
            help_lines = []
            for name in dir(self):
                if name.startswith('bzrc_'):
                    attr = getattr(self, name)
                    doc = ':%s\n' % attr.__doc__.split('\n')[0]
                    help_lines.append(doc)
            self.push(''.join(help_lines))
        else:
            name = args[1]
            func = getattr(self, 'bzrc_' + name, None)
            if func:
                doc = ':%s\n' % func.__doc__.strip()
                self.push(doc)
            else:
                self.push('fail invalid command "%s"\n' % name)

    def bzrc_shoot(self, args):
        """shoot [tankid]

        Request the tank indexed by the given parameter to fire a shot.

        Returns either:
            ok [comment]
        or:
            fail [comment]
        where the comment is optional.
        """
        try:
            command, tankid = args
            tankid = int(tankid)
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command, tankid)
        result = self.team.shoot(tankid)
        if result:
            self.push('ok\n')
        else:
            self.push('fail\n')

    def bzrc_speed(self, args):
        """speed [tankid] [speed]

        Request the tank to accelerate as quickly as possible to the
        specified speed.

        The speed is given as a multiple of maximum possible speed (1 is full
        speed). A negative parameter will cause the tank to go in reverse.
        Returns a boolean ("ok" or "fail" as described under shoot).

        Mock objects needed?
        >>> args = ['speed', '1', '1']
        >>> Handler.bzrc_speed(Handler(), args)
        fail
        """
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            self.push('fail\n')
            return
        self.ack(command, tankid, value)
        self.team.speed(tankid, value)
        self.push('ok\n')

    def bzrc_angvel(self, args):
        """angvel [tankid] [angular_velocity]

        Sets the angular velocity of the tank.

        The parameter is given as a multiple of maximum possible angular
        velocity (1 is full speed), where positive values indicate counter-
        clockwise motion, and negative values indicate clockwise motion. The
        sign is consistent with the convention use in angles in the circle.
        Returns a boolean ("ok" or "fail" as described under shoot).
        """
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            self.push('fail\n')
            return
        self.ack(command, tankid, value)
        self.team.angvel(tankid, value)
        self.push('ok\n')

    def bzrc_accelx(self, args):
        """accelx [??]

        Used specifically for freezeTag.
        """
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            self.push('fail\n')
            return
        self.ack(command, tankid, value)
        self.team.accelx(tankid, value)
        self.push('ok\n')

    def bzrc_accely(self, args):
        """accely [??]

        Used specifically for freezeTag.
        """
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            self.push('fail\n')
            return
        self.ack(command, tankid, value)
        self.team.accely(tankid, value)
        self.push('ok\n')

    def bzrc_teams(self, args):
        """teams
        Request a list of teams.

        The response will be a list, whose elements are of the form:
            team [color] [playercount]
        Color is the identifying team color/team name. Playercount is the
        number of tanks on the team.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        response = ['begin\n']
        for color,team in self.team.map.teams.items():
            response.append('team %s %d\n' % (color, len(team.tanks)))
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_obstacles(self, args):
        """obstacles

        Request a list of obstacles.

        The response is a list, whose elements are of the form:
            obstacle [x1] [y1] [x2] [y2] ...
        where (x1, y1), (x2, y2), etc. are the corners of the obstacle in
        counter-clockwise order.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        if config['no_report_obstacles']:
            self.push('fail\n')
            return

        response = ['begin\n']
        for obstacle in self.team.map.obstacles:
            response.append('obstacle')
            for x, y in obstacle.shape:
                x = random.gauss(x, self.team.posnoise)
                y = random.gauss(y, self.team.posnoise)
                response.append(' %s %s' % (x, y))
            response.append('\n')
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_occgrid(self, args):
        """occupancy grid

        Request an occupancy grid.

        Looks like:
            100,430|20,20|####
        #### = encoded 01 string
        """
        try:
            command, tankid = args
            tank = self.team.tank(int(tankid))
        except ValueError, TypeError:
            self.invalid_args(args)
            return

        if self.team.map.occgrid is None:
            raise Exception('occgrid not currently compatible with rotated '
                    'obstacles')
        if tank.status == constants.TANKDEAD:
            self.push('fail\n')
            return

        self.ack(command)

        offset_x = int(config.world.width/2)
        offset_y = int(config.world.height/2)
        width = config['occgrid_width']
        world_spos = [int(tank.pos[0]-width/2), int(tank.pos[1]-width/2)]
        world_spos[0] = max(-offset_x, world_spos[0])
        world_spos[1] = max(-offset_y, world_spos[1])
        spos = [int(tank.pos[0]+offset_x-width/2),
                int(tank.pos[1]+offset_y-width/2)]
        epos = [spos[0]+width, spos[1]+width]
        spos[0] = max(0, spos[0])
        spos[1] = max(0, spos[1])
        epos[0] = min(config.world.width, epos[0])
        epos[1] = min(config.world.height, epos[1])
        width = epos[0]-spos[0]
        height = epos[1]-spos[1]
        true_grid = self.team.map.occgrid[spos[0]:epos[0],
                spos[1]:epos[1]]

        true_positive = config['%s_true_positive' % self.team.color]
        if true_positive is None:
            true_positive = config['default_true_positive']
        true_negative = config['%s_true_negative' % self.team.color]
        if true_negative is None:
            true_negative = config['default_true_negative']

        randomized_grid = numpy.zeros((width, height))
        r_array = numpy.random.uniform(low=0, high=1, size=(width, height))
        for x in xrange(width):
            for y in xrange(height):
                occ = true_grid[x, y]
                r = r_array[x, y]
                if int(occ):
                    randomized_grid[x, y] = int(r < true_positive)
                else:
                    randomized_grid[x, y] = int(r > true_negative)

        response = ['begin\n']
        response.append('at %d,%d\n' % tuple(world_spos))
        response.append('size %dx%d\n' % (width, height))
        for row in randomized_grid:
            response.append(''.join([str(int(col)) for col in row]))
            response.append('\n')
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_bases(self, args):
        """bases

        Request a list of bases.

        The response is a list, whose elements are of the form:
            base [team color] [x1] [y1] [x2] [y2] ...
        where (x1, y1), (x2, y2), etc. are the corners of the base in counter-
        clockwise order and team color is the name of the owning team.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)

        response = ['begin\n']
        for color,base in self.team.map.bases.items():
            response.append('base %s' % color)
            for point in base.shape:
                response.append(' %s %s' % tuple(point))
            response.append('\n')
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_flags(self, args):
        """flags

        Request a list of visible flags.

        The response is a list of flag elements:
            flag [team color] [possessing team color] [x] [y]
        The team color is the color of the owning team, and the possessing
        team color is the color of the team holding the flag. If no tanks are
        carrying the flag, the possessing team is "none". The coordinate
        (x, y) is the current position of the flag. Note that the list may be
        incomplete if visibility is limited.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)

        response = ['begin\n']
        for color,team in self.team.map.teams.items():
            possess = "none"
            flag = team.flag
            if flag.tank is not None:
                possess = flag.tank.team.color
            x,y = flag.pos
            x = random.gauss(x,self.team.posnoise)
            y = random.gauss(y,self.team.posnoise)
            response.append('flag %s %s %s %s\n' % (color, possess, x, y))
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_shots(self, args):
        """shots

        Reports a list of shots.

        The response is a list of shot lines:
            shot [x] [y] [vx] [vy]
        where (c, y) is the current position of the shot and (vx, vy) is the
        current velocity.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)

        response = ['begin\n']
        for shot in self.team.map.shots():
            x, y = shot.pos
            vx, vy = shot.vel
            response.append('shot %s %s %s %s\n' % (x, y, vx, vy))
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_mytanks(self, args):
        """mytanks

        Request the status of the tanks controlled by this connection.

        The response is a list of tanks:
            mytank [index] [callsign] [status] [shots available]
                [time to reload] [flag] [x] [y] [angle] [vx] [vy] [angvel]
        Index is the 0 based index identifying this tank. This index is used
        for instructions. The callsign is the tank's unique identifier within
        the game. The status is a string like "alive," "dead," etc. Shots
        available is the number of shots remaining before a reload delay. Flag
        is the color/name of the flag being held, or "-" if none is held. The
        coordinate (x, y) is the current position. Angle is the direction the
        tank is pointed, between negative pi and pi. The vector (vx, vy) is
        the current velocity of the tank, and angvel is the current angular
        velocity of the tank (in radians per second).
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)

        response = ['begin\n']
        entry_template = ('mytank %(id)s %(callsign)s %(status)s'
                ' %(shots_avail)s %(reload)s %(flag)s %(x)s %(y)s %(angle)s'
                ' %(vx)s %(vy)s %(angvel)s\n')
        for i, tank in enumerate(self.team.tanks):
            data = {}
            data['id'] = i
            data['callsign'] = tank.callsign
            data['status'] = tank.status
            # WARNING: there's an evil hard-coded constant here!
            data['shots_avail'] = 10-len(tank.shots)
            data['reload'] = tank.reloadtimer
            data['flag'] = tank.flag and tank.flag.team.color or '-'
            data['x'] = int(tank.pos[0])
            data['y'] = int(tank.pos[1])
            data['angle'] = tank.rot
            data['vx'],data['vy'] = tank.velocity()
            data['angvel'] = tank.angvel
            response.append(entry_template % data)
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_othertanks(self, args):
        """othertanks

        Request the status of other tanks in the game (those not
        controlled by this connection.

        The response is a list of tanks:
            othertank [callsign] [color] [status] [flag] [x] [y] [angle]
        where callsign, status, flag, x, y, and angle are as described under
        mytanks and color is the name of the team color.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)

        response = ['begin\n']
        entry_template = ('othertank %(callsign)s %(color)s %(status)s'
                ' %(flag)s %(x)s %(y)s %(angle)s\n')
        for color,team in self.team.map.teams.items():
            if team == self.team:
                continue
            for tank in team.tanks:
                data = {}
                data['color'] = color
                data['callsign'] = tank.callsign
                data['status'] = tank.status
                # WARNING: there's an evil hard-coded constant here!
                data['shots_avail'] = 10-len(tank.shots)
                data['reload'] = tank.reloadtimer
                data['flag'] = tank.flag and tank.flag.team.color or '-'

                x, y = tank.pos
                data['x'] = random.gauss(x, self.team.posnoise)
                data['y'] = random.gauss(y, self.team.posnoise)

                angle = random.gauss(tank.rot, self.team.angnoise) % math.pi*2
                if angle > math.pi:
                    angle -= math.pi*2
                data['angle'] = angle

                vx,vy = tank.velocity()
                data['vx'] = random.gauss(vx, self.team.velnoise)
                data['vy'] = random.gauss(vy, self.team.velnoise)

                data['angvel'] = tank.angvel

                response.append(entry_template % data)

        response.append('end\n')
        self.push(''.join(response))

    def bzrc_constants(self, args):
        """constants

        Request a list of constants.

        These constants define the rules of the game and the behavior of the
        world. The response is a list:
            constant [name] [value]
        Name is a string. Value may be a number or a string. Boolean values
        are 0 or 1.
        """
        # TODO: is it possible to simply iterate through all constants without
        # specifically referencing each one?
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        true_positive = config['%s_true_positive' % self.team.color]
        if true_positive is None:
            true_positive = config['default_true_positive']
        true_negative = config['%s_true_negative' % self.team.color]
        if true_negative is None:
            true_negative = config['default_true_negative']
        self.ack(command)
        ## is this the best way to do this? hard coding it in?
        response = ['begin\n',
            'constant team %s\n' % (self.team.color),
            'constant worldsize %s\n' % (config['world_size']),
            # WARNING: there's an evil hard-coded constant here!
            'constant hoverbot %s\n' % (0),
            'constant puppyzone %s\n' % (config['puppy_guard_zone']),
            'constant tankangvel %s\n' % (constants.TANKANGVEL),
            'constant tanklength %s\n' % (constants.TANKLENGTH),
            'constant tankradius %s\n' % (constants.TANKRADIUS),
            'constant tankspeed %s\n' % (constants.TANKSPEED),
            'constant tankalive %s\n' % (constants.TANKALIVE),
            'constant tankdead %s\n' % (constants.TANKDEAD),
            'constant linearaccel %s\n' % (constants.LINEARACCEL),
            'constant angularaccel %s\n' % (constants.ANGULARACCEL),
            'constant tankwidth %s\n' % (constants.TANKWIDTH),
            'constant shotradius %s\n' % (constants.SHOTRADIUS),
            'constant shotrange %s\n' % (constants.SHOTRANGE),
            'constant shotspeed %s\n' % (constants.SHOTSPEED),
            'constant flagradius %s\n' % (constants.FLAGRADIUS),
            'constant explodetime %s\n' % (constants.EXPLODETIME),
            'constant truepositive %s\n' % (true_positive),
            'constant truenegative %s\n' % (true_negative),
            'end\n']
        self.push(''.join(response))

    def bzrc_scores(self, args):
        """scores

        Request the scores of all teams.  The response is a list of scores,
        one for each team pair:
            score [team_i] [team_j] [score]

        Notice that a team generates no score when compared against itself.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        self.push('fail not implemented\n')
        return

        response = ['begin\n']
        for team1 in self.team.map.teams:
            for team2 in self.team.map.teams:
                if team1 != team2:
                    team1_name = constants.COLORNAME[team1.color]
                    team2_name = constants.COLORNAME[team2.color]
                    # Score not implemented (?)
                    score = 0
                    response.append('score %s %s %s'
                            % (team1_name, team2_name, score))
                    response.append('\n')
        response.append('end\n')
        self.push(''.join(response))

    def bzrc_timer(self, args):
        """timer

        Requests how much time has passed and what time limit exists.

            timer [time elapsed] [time limit]

        Time elapsed is the number of seconds that the server has been alive,
        while time limit is the given limit. Once the limit is reached, the
        server will stop updating the game.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        timespent = self.team.map.timespent
        timelimit = self.team.map.timelimit
        self.push('timer %s %s\n' % (timespent, timelimit))

    def bzrc_quit(self, args):
        """quit

        Disconnects the session.

        This is technically an extension to the BZRC protocol.  We should
        really backport this to BZFlag.
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        self.push('ok\n')
        self.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
