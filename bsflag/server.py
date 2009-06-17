"""BSFlag BZRC Server

The Server object listens on a port for incoming connections.  When a client
connects, the Server dispatches its connection to a new Handler.
"""

import asynchat
import asyncore
import math
import socket
import time
import random

import constants

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
        self.bind(addr)
        self.listen(BACKLOG)

    def handle_accept(self):
        sock, addr = self.accept()
        if self.in_use:
            sock.close()
        else:
            self.in_use = True
            Handler(sock, self.team, self.handle_closed_handler)

    def handle_closed_handler(self):
        self.in_use = False


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

    def found_terminator(self):
        """Called when Asynchat finds an end-of-line.

        Note that Asynchat ensures that our input buffer contains everything
        up to but not including the newline character.
        """
        args = self.input_buffer.split()
        self.input_buffer = ''
        if args:
            if self.established:
                try:
                    command = getattr(self, 'bzrc_%s' % args[0])
                except AttributeError:
                    self.push('fail Invalid command\n')
                    return
                command(args)
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

    def bzrc_shoot(self, args):
        """Request the tank indexed by the given parameter to fire a shot.

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
        """Request the tank to accelerate as quickly as possible to the 
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
        """Sets the angular velocity of the tank.

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
        """Used specifically for freezeTag."""
        pass

    def bzrc_accely(self, args):
        """Used specifically for freezeTag."""
        pass

    def bzrc_teams(self, args):
        """Request a list of teams.

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
        for team in self.team.mapper.teams:
            color = team.color_name()
            # TODO: javariffic?
            playercount = 0
            for tank in team.tanks:
                playercount = playercount + 1
            self.push('team %s %s\n' % (color, playercount))
        self.push('end\n')

    def bzrc_obstacles(self, args):
        """Request a list of obstacles.

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
        for obstacle in self.team.mapper.obstacles:
            self.push('obstacle')
            for corner in obstacle.corners:
                x, y = corner
                self.push(' %s %s' % (x, y))
            self.push('\n')
        self.push('end\n')

    def bzrc_bases(self, args):
        """Request a list of bases.

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
        for base in self.team.mapper.bases:
            self.push('base %s' % constants.COLORNAME[base.color])
            for corner in base.corners:
                x, y = corner
                self.push(' %s %s' % (x, y))
            self.push('\n')
        self.push('end\n')

    def bzrc_flags(self, args):
        """Request a list of visible flags.

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
        for flag in self.team.mapper.iter_flags():
            x, y = flag.pos
            color = constants.COLORNAME[flag.color]
            possess = "none"
            if flag.tank is not None:
                possess = constants.COLORNAME[flag.tank.color]
            self.push('flag %s %s %s %s\n' % (color, possess, x, y))
        self.push('end\n')

    def bzrc_shots(self, args):
        """Reports a list of shots.

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
        for shot in self.team.mapper.iter_shots():
            x, y = shot.pos
            vx, vy = shot.vel
            self.push('shot %s %s %s %s\n' % (x, y, vx, vy))
        self.push('end\n')

    def bzrc_mytanks(self, args):
        """Request the status of the tanks controlled by this connection.

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
            index = i
            callsign = tank.callsign
            status = tank.status
            shotsleft = self.team.mapper.maximum_shots - len(tank.shots)
            reloadtime = constants.RELOADTIME - tank.reloadtime
            # no negative reload time
            if reloadtime < 0:
                reloadtime = 0.0
            flag = None
            if tank.flag != None:
                flag = constants.COLORNAME[tank.flag.color]
            else:
                flag = '-'
            x, y = tank.pos
            #if not isinstance(x, float):
            #    print 'x is not float: %s' % x
            angle = tank.rot
            if abs(angle) > math.pi:
                pi_units = 0
                while abs(angle) > math.pi:
                    pi_units = pi_units + 1
                    angle = abs(angle) - math.pi
                if pi_units % 2 == 1:
                    angle = math.pi - angle
                    angle = angle * -1
            vx, vy = tank.vel
            angvel = tank.angvel
            self.push('mytank %s %s %s ' % (index, callsign, status))
            self.push('%s %s %s ' % (shotsleft, reloadtime, flag))
            self.push('%s %s %s %s %s %s\n' % (x, y, angle, vx, vy, angvel))
        self.push('end\n')

    def bzrc_othertanks(self, args):
        """ Request the status of other tanks in the game (those not 
        controlled by this connection.

        The response is a list of tanks:
            othertank [callsign] [color] [flag] [x] [y] [angle]
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
        for team in self.team.mapper.teams:
            if team.color == self.team.color:
                continue
            for tank in team.tanks:
                callsign = tank.callsign
                color = constants.COLORNAME[tank.color]
                status = tank.status
                flag = None
                if tank.flag != None:
                    flag = constants.COLORNAME[tank.flag.color]
                else:
                    flag = '-'
                x, y = tank.pos
                angle = tank.rot
                if abs(angle) > math.pi:
                    pi_units = 0
                    while abs(angle) > math.pi:
                        pi_units = pi_units + 1
                        angle = abs(angle) - math.pi
                    if pi_units % 2 == 1:
                        angle = math.pi - angle
                        angle = angle * -1
                self.push('othertank %s %s %s ' % (callsign, color, status))
                self.push('%s %s %s %s\n' % (flag, x, y, angle))
        self.push('end\n')

    def bzrc_constants(self, args):
        """Request a list of constants.

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
        self.push('begin\n')
        self.push('constant team %s\n' % (constants.COLORNAME[self.team.color]))
        self.push('constant worldsize %s\n' % (constants.WORLDSIZE))
        self.push('constant hoverbot %s\n' % (self.team.mapper.hoverbot))
        self.push('constant TANKANGVEL %s\n' % (constants.TANKANGVEL))
        self.push('constant TANKLENGTH %s\n' % (constants.TANKLENGTH))
        self.push('constant TANKRADIUS %s\n' % (constants.TANKRADIUS))
        self.push('constant TANKSPEED %s\n' % (constants.TANKSPEED))
        self.push('constant LINEARACCEL %s\n' % (constants.LINEARACCEL))
        self.push('constant ANGULARACCEL %s\n' % (constants.ANGULARACCEL))
        self.push('constant TANKWIDTH %s\n' % (constants.TANKWIDTH))
        self.push('constant SHOTRADIUS %s\n' % (constants.SHOTRADIUS))
        self.push('constant SHOTRANGE %s\n' % (constants.SHOTRANGE))
        self.push('constant FLAGRADIUS %s\n' % (constants.FLAGRADIUS))
        self.push('constant EXPLODETIME %s\n' % (constants.EXPLODETIME))
        self.push('end\n')

    def bzrc_scores(self, args):
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        self.push('begin\n')
        for team in self.team.mapper.teams:
            self.push('\t%s' % (constants.COLORNAME[team.color]))
        self.push('\n')
        for team in self.team.mapper.teams:
            self.push('%s' % (constants.COLORNAME[team.color]))
            for score in team.iter_ctf_scores():
                self.push('\t%s' % (score))
            self.push('\n')
        self.push('end\n')
        
    def bzrc_timer(self, args):
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command)
        timespent = self.team.mapper.timespent
        timelimit = self.team.mapper.timelimit
        self.push('timer %s %s\n' % (timespent, timelimit))

    def bzrc_quit(self, args):
        """Disconnects the session.

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
        """All tanks shoot (cheat).
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        for team in self.team.mapper.teams:
            for i in xrange(0, len(team.tanks)):
                team.shoot(i)

    def bzrc_hammertime(self, args):
        """All tanks shoot (cheat).
        """
        try:
            command, = args
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        for team in self.team.mapper.teams:
            for tank in team.tanks:
                tank.givenspeed = random.uniform(-1, 1)
                tank.angvel = random.uniform(-1, 1)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
