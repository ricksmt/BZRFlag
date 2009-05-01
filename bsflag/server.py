"""BSFlag BZRC Server"""

import asynchat
import asyncore
import socket

ADDRESS = ('127.0.0.1', 4001)
BACKLOG = 5


class Server(asyncore.dispatcher):
    def __init__(self):
        sock = socket.socket()
        asyncore.dispatcher.__init__(self, sock)
        self.bind(ADDRESS)
        self.listen(BACKLOG)

    def handle_accept(self):
        sock, addr = self.accept()
        Handler(sock)


class Handler(asynchat.async_chat):
    """Server which implements the BZRC protocol.

    Each team has its own server.
    """
    def __init__(self, *args):
        asynchat.async_chat.__init__(self, *args)
        self.set_terminator('\n')
        self.input_buffer = []
        self.push('bzrobots 1\n')

    def collect_incoming_data(self, chunk):
        self.input_buffer.append(chunk)

    def found_terminator(self):
        data = ''.join(self.input_buffer)
        self.input_buffer = []

        lines = data.split('\n')
        requests = lines[:-1]
        remainder = lines[-1]
        if remainder:
            self.input_buffer.append(remainder)

        for request in requests:
            print 'request:', request


s = Server()
asyncore.loop()


# vim: et sw=4 sts=4
