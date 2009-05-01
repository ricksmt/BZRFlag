"""BSFlag Networking

The IOMap implements a simple interface for select with callbacks to handlers.
This allows for efficient non-blocking non-threaded networking code.
"""

import errno
import select
import socket
import sys

BACKLOG = 10
BUFFER_SIZE = 1 << 16


class IOMap(object):
    """A manager for file descriptors and their associated handlers.

    The poll method dispatches events to the appropriate handlers.
    """
    def __init__(self):
        self.readmap = {}
        self.writemap = {}

    def register_read(self, fd, handler):
        """Registers an IO handler for a file descriptor for reading."""
        self.readmap[fd] = handler

    def register_write(self, fd, handler):
        """Registers an IO handler for a file descriptor for writing."""
        self.writemap[fd] = handler

    def unregister_read(self, fd):
        """Unregisters the given file descriptor for reading."""
        if fd in self.readmap:
            del self.readmap[fd]

    def unregister_write(self, fd):
        """Unregisters the given file descriptor for writing."""
        if fd in self.writemap:
            del self.writemap[fd]

    def poll(self, timeout=None):
        """Performs a poll and dispatches the resulting events."""
        if not self.readmap and not self.writemap:
            return
        rlist = list(self.readmap)
        wlist = list(self.writemap)
        try:
            rlist, wlist, _ = select.select(rlist, wlist, [], timeout)
        except select.error, e:
            errno, message = e.args
            if errno == EINTR:
                return
            else:
                raise
        for fd in rlist:
            handler = self.readmap[fd]
            handler(fd, self)
        for fd in wlist:
            handler = self.writemap[fd]
            handler(fd, self)


class Server(object):
    """A server that listens for incoming BZRC connections."""

    def __init__(self, addr, iomap):
        self.sock = socket.socket()
        self.sock.bind(addr)
        self.sock.listen(BACKLOG)
        iomap.register_read(self.sock.fileno(), self.handle_read)

    def handle_read(self, fd, iomap):
        """Accepts and dispatches a single new connection."""
        try:
            client_sock, _ = self.sock.accept()
        except (OSError, IOError), e:
            if e.errno != errno.EINTR:
                error = os.strerror(e.errno)
                print >>sys.stderr, "Socket error in accept:", error
                iomap.unregister_read(fd)
                iomap.unregister_write(fd)
                self.sock.close()
                return
        conn = Connection(client_sock, iomap)


class Connection(object):
    """An object that manages the connection with a remote BZRC client.
    
    It keeps track of an rbuffer for reading and a wbuffer for writing.  Both
    buffers are strings.
    """
    def __init__(self, sock, iomap):
        self.sock = sock
        iomap.register_read(self.sock.fileno(), self.handle_read)
        self.rbuffer = ''
        self.wbuffer = ''

    def handle_read(self, fd, iomap):
        try:
            data = os.read(fd, BUFFER_SIZE)
        except (OSError, IOError), e:
            if e.errno != errno.EINTR:
                error = os.strerror(e.errno)
                print >>sys.stderr, "Read error:", error
                iomap.unregister_read(fd)
                iomap.unregister_write(fd)
                self.sock.close()
            return
        self.rbuffer += data

    def handle_write(self, fd, iomap):
        try:
            count = os.write(fd, self.wbuffer)
        except (OSError, IOError), e:
            if e.errno != errno.EINTR:
                error = os.strerror(e.errno)
                print >>sys.stderr, "Write error:", error
                iomap.unregister_read(fd)
                iomap.unregister_write(fd)
                self.sock.close()
            return
        if count:
            self.wbuffer = self.wbuffer[:count]
        if not self.wbuffer:
            self.unregister_write(fd)

    def write(self, data):
        self.wbuffer += data
        self.register_write(self.sock.fileno())


# vim: et sw=4 sts=4
