"""BSFlag BZRC Server"""

import asynchat
import asyncore
import socket
import time

BACKLOG = 5


class Server(asyncore.dispatcher):
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
    """Server which implements the BZRC protocol.

    Each team has its own server.
    """
    def __init__(self, sock, team, closed_callback):
        asynchat.async_chat.__init__(self, sock)
        self.team = team
        self.closed_callback = closed_callback
        self.set_terminator('\n')
        self.input_buffer = ''
        self.push('bzrobots 1\n')
        self.init_timestamp = time.time()

    def handle_close(self):
        self.closed_callback()
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
            try:
                command = getattr(self, 'bzrc_%s' % args[0])
            except AttributeError:
                self.push('fail Invalid command\n')
                return
            command(args)

    def invalid_args(self, args):
        self.ack(*args)
        self.push('fail Invalid parameter(s)\n')

    def ack(self, *args):
        timestamp = time.time() - self.init_timestamp
        arg_string = ' '.join(str(arg) for arg in args)
        self.push('ack %s %s\n' % (timestamp, arg_string))

    def bzrc_shoot(self, args):
        """Requests the tank to shoot."""
        try:
            command, tankid = args
            tankid = int(tankid)
        except ValueError, TypeError:
            self.invalid_args(args)
            return

        self.ack(command, tankid)
        self.team.shoot(tankid)

    def bzrc_angvel(self, args):
        """Sets the angular velocity of the tank."""
        try:
            command, tankid, value = args
            tankid = int(tankid)
            value = float(value)
        except ValueError, TypeError:
            self.invalid_args(args)
            return

        self.ack(command, tankid, value)
        self.team.angvel(tankid, value)


# vim: et sw=4 sts=4
