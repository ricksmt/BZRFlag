#!/usr/bin/env python
from cStringIO import StringIO
import asyncore
import os
import unittest

from bzrflag import server, config

LISTEN_SOCK_FILENO = 5
CONN_SOCK_1_FILENO = 11
CONN_SOCK_2_FILENO = 12


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.sock = MockSocket(CONN_SOCK_1_FILENO)

        self.config = {'telnet_console': False}
        team = MockTeam()
        self.map = None
        self.handle_closed_handler = MockHandleClosedHandler()
        self.handler = server.Handler(self.sock, team, map,
                self.handle_closed_handler, self.config, {})

    def tearDown(self):
        del self.sock
        del self.config
        del self.map
        del self.handle_closed_handler
        del self.handler

    def testHandshake(self):
        # Trigger the handler to write its handshake.
        asyncore.write(self.handler)
        self.assertEquals(self.sock.remote_read(), 'bzrobots 1\n')

        #asyncore.read(self.sock)
        #self.sock.remote_send('


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.conn_sock_1 = MockSocket(CONN_SOCK_1_FILENO)
        self.conn_sock_2 = MockSocket(CONN_SOCK_2_FILENO)
        socks = [self.conn_sock_1, self.conn_sock_2]
        listen_sock = MockListenSocket(LISTEN_SOCK_FILENO, socks)

        self.config = {'telnet_console': False}
        address = None
        team = MockTeam()
        map = None
        self.asyncore_map = {}
        self.srv = server.Server(address, team, map, self.config,
                listen_sock, self.asyncore_map)

    def tearDown(self):
        del self.conn_sock_1
        del self.conn_sock_2
        del self.config
        del self.asyncore_map

    def testAccept(self):
        self.assertEquals(self.srv.in_use, False)

        # Trigger an accept.
        asyncore.read(self.srv)
        self.assertTrue(CONN_SOCK_1_FILENO in self.asyncore_map)

        self.assertEquals(self.srv.in_use, True)

        # Trigger a second accept, which should fail.
        asyncore.read(self.srv)
        self.assertTrue(self.conn_sock_2.closed)

    def testHandshake(self):
        # Trigger an accept.
        asyncore.read(self.srv)
        handler = self.asyncore_map[CONN_SOCK_1_FILENO]

        # Trigger the handler to write its handshake.
        asyncore.write(handler)
        self.assertEquals(self.conn_sock_1.remote_read(), 'bzrobots 1\n')


class MockTeam(object):
    color = 'polkadot'


class MockListenSocket(object):
    def __init__(self, fileno, socks):
        self._fileno = fileno
        self.socks = socks

    def accept(self):
        sock = self.socks.pop(0)
        #print 'socket!!', sock
        return sock, None

    def fileno(self):
        return self._fileno

    def __getattr__(self, name):
        """Catchall do-nothing"""
        return (lambda *args: None)


class MockSocket(object):
    def __init__(self, fileno):
        self._fileno = fileno
        self.inbuf = ''
        self.outbuf = ''
        self.closed = False

    def fileno(self):
        return self._fileno

    def close(self):
        self.closed = True

    def recv(self, buflen):
        data = self.inbuf[:buflen]
        self.inbuf = self.inbuf[buflen:]
        return data

    def send(self, data):
        self.outbuf += str(data)
        return len(data)

    def remote_recv(self, buflen):
        data = self.outbuf[:buflen]
        self.outbuf = self.outbuf[buflen:]
        return data

    def remote_send(self, data):
        self.inbuf += str(data)
        return len(data)

    def remote_read(self):
        """Read everything in the buffer, for convenience in testing."""
        data = self.outbuf
        self.outbuf = ''
        return data

    def __getattr__(self, name):
        """Catchall do-nothing"""
        return (lambda *args: None)


class MockHandleClosedHandler(object):
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

# vim: et sw=4 sts=4
