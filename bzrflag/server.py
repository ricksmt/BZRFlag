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
logger = logging.getLogger('server')

import constants
import config

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
        if config.config['telnet_console']:
            self.team.map.game.display.console.write(self.team.color + ' > ' + text)
            logger.debug(self.team.color + ' > ' + text)
        if text.startswith('fail '):
            logger.error(self.team.color + ' > ' + text)
        

    def found_terminator(self):
        """Called when Asynchat finds an end-of-line.

        Note that Asynchat ensures that our input buffer contains everything
        up to but not including the newline character.
        """
        if not config.config['python_console']:
            self.team.map.game.display.console.write(self.team.color + ' : ' + self.input_buffer + '\n')
        logger.debug(self.team.color + ' : ' + self.input_buffer + '\n')
        args = self.input_buffer.split()
        self.input_buffer = ''
        if args:
            if self.established:
                try:
                    command = getattr(self, 'bzrc_%s' % args[0])
                except AttributeError:
                    self.push('fail Invalid command\n')
                    return
                try:
                    command(args)
                except Exception, e:
                    self.push('fail '+str(e)+'\n')
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

    def bzrc_help(self, args):
        """help [command]
        if not command is given, list the commands
        otherwise, return specific help for a command"""
        if len(args)==1:
            res = '\n'.join(':'+getattr(self,i).__doc__.split('\n')[0] for i in dir(self) if i.startswith('bzrc_'))
            self.push(res+'\n')
        else:
            func = getattr(self,'bzrc_'+args[1],None)
            if func:
                self.push(':'+func.__doc__.strip()+'\n')
            else:
                self.push('fail invalid command "%s"\n'%args[1])

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
        self.push('begin\n')
        for color,team in self.team.map.teams.items():
            self.push('team %s %d\n'%(color, len(team.tanks)))
        self.push('end\n')

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
        self.push('begin\n')
        for obstacle in self.team.map.obstacles:
            self.push('obstacle')
            for point in obstacle.shape:
                self.push(' %s %s' % tuple(point))
            self.push('\n')
        self.push('end\n')

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
        self.push('begin\n')
        for color,base in self.team.map.bases.items():
            self.push('base %s' % color)
            for point in base.shape:
                self.push(' %s %s' % tuple(point))
            self.push('\n')
        self.push('end\n')

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
        self.push('begin\n')
        for color,team in self.team.map.teams.items():
            possess = "none"
            flag = team.flag
            if flag.tank is not None:
                possess = flag.tank.team.color
            self.push('flag %s %s %s %s\n' % ((color, possess)+tuple(flag.pos)))
        self.push('end\n')

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
        self.push('begin\n')
        for shot in self.team.map.shots():
            x, y = shot.pos
            vx, vy = shot.vel
            self.push('shot %s %s %s %s\n' % (x, y, vx, vy))
        self.push('end\n')

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
        self.push('begin\n')
        for i in xrange (len(self.team.tanks)):
            tank = self.team.tanks[i]
            data = {'id':i}
            data['callsign'] = tank.callsign
            data['status'] = tank.status
            data['shots_avail'] = 10-len(tank.shots)
            data['reload'] = tank.reloadtimer
            data['flag'] = tank.flag and tank.flag.team.color or '-'
            data['x'],data['y'] = tank.pos
            data['angle'] = tank.rot
            data['vx'],data['vy'] = tank.velocity()
            data['angvel'] = tank.angvel

            self.push("mytank %(id)s %(callsign)s %(status)s %(shots_avail)s\
 %(reload)s %(flag)s %(x)s %(y)s %(angle)s %(vx)s %(vy)s %(angvel)s\n"%data)

        self.push('end\n')

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
        self.push('begin\n')
        for color,team in self.team.map.teams.items():
            if team == self.team:continue
            for tank in team.tanks:
                data = {'color':color}
                data['callsign'] = tank.callsign
                data['status'] = tank.status
                data['shots_avail'] = 10-len(tank.shots)
                data['reload'] = tank.reloadtimer
                data['flag'] = tank.flag and tank.flag.team.color or '-'

                x, y = tank.pos
                x = random.gauss(x, self.team.posnoise)
                y = random.gauss(y, self.team.posnoise)
                data['x'],data['y'] = x, y
                
                angle = random.gauss(tank.rot, self.team.angnoise) % math.pi*2
                if angle > math.pi:
                    angle -= math.pi*2
                data['angle'] = angle

                vx,vy = tank.velocity()
                vx = random.gauss(vx, self.team.velnoise)
                vy = random.gauss(vy, self.team.velnoise)
                data['vx'],data['vy'] = vx, vy

                data['angvel'] = tank.angvel

                self.push("othertank %(callsign)s %(color)s %(status)s " % data)
                self.push("%(flag)s %(x)s %(y)s %(angle)s\n"%data)
        self.push('end\n')

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
        self.ack(command)
        ## is this the best way to do this? hard coding it in?
        self.push('begin\n')
        self.push('constant team %s\n' % (self.team.color))
        self.push('constant worldsize %s\n' % (constants.WORLDSIZE))
        self.push('constant hoverbot %s\n' % (0))
        self.push('constant tankangvel %s\n' % (constants.TANKANGVEL))
        self.push('constant tanklength %s\n' % (constants.TANKLENGTH))
        self.push('constant tankradius %s\n' % (constants.TANKRADIUS))
        self.push('constant tankspeed %s\n' % (constants.TANKSPEED))
        self.push('constant tankalive %s\n' % (constants.TANKALIVE))
        self.push('constant tankdead %s\n' % (constants.TANKDEAD))
        self.push('constant linearaccel %s\n' % (constants.LINEARACCEL))
        self.push('constant angularaccel %s\n' % (constants.ANGULARACCEL))
        self.push('constant tankwidth %s\n' % (constants.TANKWIDTH))
        self.push('constant shotradius %s\n' % (constants.SHOTRADIUS))
        self.push('constant shotrange %s\n' % (constants.SHOTRANGE))
        self.push('constant flagradius %s\n' % (constants.FLAGRADIUS))
        self.push('constant explodetime %s\n' % (constants.EXPLODETIME))
        self.push('end\n')

    def bzrc_scores(self, args):
        """scores
        Request the scores of all teams. A score is generated for each team
        pair in a table:

                       [team 1]   [team 2]   ...
            [team 1]      0       [score]    ...
            [team 2]   [score]       0       ...

        Notice that a team generates no score when compared against itself.
        """
        self.push('fail not implemented\n')
        '''try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        self.push('begin\n')
        for team in self.team.map.teams:
            self.push('\t%s' % (constants.COLORNAME[team.color]))
        self.push('\n')
        for team in self.team.map.teams:
            self.push('%s' % (constants.COLORNAME[team.color]))
            for score in team.iter_ctf_scores():
                self.push('\t%s' % (score))
            self.push('\n')
        self.push('end\n')'''

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
        self.close()

    def bzrc_fireatwill(self, args):
        """fireatwill
        All tanks shoot (cheat).
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        for team in self.team.map.teams.values():
            for i in xrange(0, len(team.tanks)):
                team.shoot(i)

    def bzrc_hammertime(self, args):
        """hammertime
        All tanks move (cheat).
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        for team in self.team.map.teams.values():
            for tank in team.tanks:
                tank.givenspeed = random.uniform(-1, 1)
                tank.angvel = random.uniform(-1, 1)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
