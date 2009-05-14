"""BSFlag BZRC Server

The Server object listens on a port for incoming connections.  When a client
connects, the Server dispatches its connection to a new Handler.
"""

import asynchat
import asyncore
import socket
import time

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
        self.team.shoot(tankid)


    def bzrc_speed(self, args):
        """Request the tank to accelerate as quickly as possible to the 
        specified speed.

        The speed is given as a multiple of maximum possible speed (1 is full
        speed). A negative parameter will cause the tank to go in reverse.
        Returns a boolean ("ok" or "fail" as described under shoot).
        """
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            return
        self.ack(command, tankid, value)
        self.team.speed(tankid, value)

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
            return
        self.ack(command, tankid, value)
        self.team.angvel(tankid, value)

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
        for team in self.team.game.iter_teams():
            color = team.color_name()
            # TODO: javariffic?
            playercount = 0
            for tank in self.team.iter_tanks():
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
        for item in self.team.game.iter_boxes():
            self.push('obstacle')
            for corner in self.team.game.iter_corners(item):
                self.push(' %s %s' % (corner[0], corner[1]))
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
        for item in self.team.game.iter_bases():
            self.push('base %s' % constants.COLORNAME[item.color])
            for corner in self.team.game.iter_corners(item):
                self.push(' %s %s' % (corner[0], corner[1]))
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
        pass

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
        for shot in self.team.game.iter_shots():
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
        pass

    def bzrc_othertanks(self, args):
        """ Request the status of other tanks in the game (those not 
        controlled by this connection.

        The response is a list of tanks:
            othertank [callsign] [color] [flag] [x] [y] [angle]
        where callsign, status, flag, x, y, and angle are as described under
        mytanks and color is the name of the team color.
        """
        pass

    def bzrc_constants(self, args):
        """Request a list of constants.

        These constants define the rules of the game and the behavior of the
        world. The response is a list:
            constant [name] [value]
        Name is a string. Value may be a number or a string. Boolean values
        are 0 or 1.
        """
        pass

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


# vim: et sw=4 sts=4
