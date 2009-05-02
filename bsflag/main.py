"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import asyncore
import os
import socket
import sys

import constants
import server

# A higher loop timeout increases CPU usage but decreases the frame rate.
LOOP_TIMEOUT = 0.01


def options():
    import optparse
    p = optparse.OptionParser()
    p.add_option('--world', action='store', dest='world')
    p.add_option('--port', action='store', type='int', dest='port', default=0)
    opts, args = p.parse_args()
    if args:
        p.parse_error('No positional arguments are allowed.')
    return opts


def run():
    opts = options()

    from world import World
    if opts.world:
        f = open(opts.world)
        parser = World.parser()
        results = parser.parseString(f.read())
        world = results[0]
    else:
        world = World()


    # TODO: create one server per color.
    addr = ('0.0.0.0', opts.port)
    try:
        bzrc = server.Server(addr)
    except socket.error, e:
        print >>sys.stderr, 'Socket error:', os.strerror(e.errno)
        sys.exit(1)

    host, port = bzrc.socket.getsockname()
    print 'Listening on port %s.' % port


    # TODO: Move most or all of the graphics stuff to another function.
    import graphics
    display = graphics.Display(world)
    display.setup()

    shot = Shot()
    display.shot_sprite(shot)

    tank = Tank()
    display.tank_sprite(tank)

    while True:
        asyncore.loop(LOOP_TIMEOUT, count=1)

        shot.update()
        tank.update()
        display.update()


class Shot(object):
    color = 1
    size = (constants.ShotRadius,) * 2
    pos = (-400, 0)
    rot = None

    def update(self):
        x, y = self.pos
        self.pos = (x + 1), y


class Tank(object):
    color = 1
    size = (constants.TankRadius,) * 2
    pos = (-400, 200)
    rot = None

    def update(self):
        x, y = self.pos
        self.pos = (x + 1), y


# vim: et sw=4 sts=4
