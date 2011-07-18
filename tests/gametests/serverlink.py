#!/usr/bin/python -tt

from __future__ import division

import math
import sys
import socket
import time
import numpy


class Link:
    """Class handles queries and responses with bzrflag server."""

    def __init__(self, host, port):
        """Connect to server with given hostname and port."""
        sock = socket.socket()
        sock.connect((host, port))
        self.conn = sock.makefile(bufsize=1)
        self.handshake()
    
    def handshake(self):
        """Perform handshake with server."""
        self.expect(('bzrobots', '1'), True)
        print >>self.conn, 'agent 1'

    def close(self):
        """Close socket."""
        self.conn.close()

    def read_arr(self):
        """Read response from server as an array split on whitespace."""
        try:
            line = self.conn.readline()
        except socket.error:
            print "Server Shut down. Aborting"
            sys.exit(1)
        return line.split()

    def sendline(self, line):
        """Send a line to server."""
        print >>self.conn, line

    def die_confused(self, expected, got_arr):
        """When we think the server should have responded differently, call
        this method with a string explaining what should have been sent and
        with the array containing what was actually sent.
        
        """
        raise UnexpectedResponse(expected, ' '.join(got_arr))

    def expect(self, expected, full=False):
        """Verify that server's response is as expected."""
        if isinstance(expected, str):
            expected = (expected,)
        line = self.read_arr()
        good = True
        
        if full and len(expected) != len(line):
            good = False
        else:
            for a,b in zip(expected,line):
                if a!=b:
                    good = False
                    break
                    
        if not good:
            self.die_confused(' '.join(expected), line)
        if full:
            return True
        return line[len(expected):]
    
    def expect_multi(self, *expecteds, **kwds):
        """Verify the server's response looks like one of
        several possible responses.  Return the index of the matched response,
        and the server's line response.
        
        """
        line = self.read_arr()
        for i,expected in enumerate(expecteds):
            for a,b in zip(expected, line):
                if a!=b:
                    break
            else:
                if not kwds.get('full',False) or len(expected) == len(line):
                    break
        else:
            self.die_confused(' or '.join(' '.join(one) for one in expecteds),
                    line)
        return i, line[len(expected):]

    def read_ack(self):
        """Expect an "ack" line from the server.

        Raise an UnexpectedResponse exception if anything else.
        
        """
        self.expect('ack')

    def read_bool(self):
        """Expect a boolean response from the server.

        Return True or False in accordance with the response.  Raise an
        UnexpectedResponse exception if anything else.
        
        """
        i, rest = self.expect_multi(('ok',),('fail',))
        return (True, False)[i]


class UnexpectedResponse(Exception):
    """Exception raised when Link recieves an unexpected response."""

    def __init__(self, expected, got):
        self.expected = expected
        self.got = got

    def __str__(self):
        return 'Link: Expected "%s".  Instead got "%s".' % (self.expected,
                self.got)


# vim: et sw=4 sts=4
