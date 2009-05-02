"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import asyncore
import os
import socket
import sys

import game
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

    # Create team 1.
    team = game.Team(1)

    # Create the server for team 1.
    addr = ('0.0.0.0', opts.port)
    try:
        bzrc = server.Server(addr, team)
    except socket.error, e:
        print >>sys.stderr, 'Socket error:', os.strerror(e.errno)
        sys.exit(1)
    host, port = bzrc.socket.getsockname()
    print 'Listening on port %s.' % port


    # TODO: Move most or all of the graphics stuff to another function.
    import graphics
    display = graphics.Display(world)
    display.setup()

    shot = game.Shot()
    display.shot_sprite(shot)

    for tank in team:
        display.tank_sprite(tank)

    while True:
        asyncore.loop(LOOP_TIMEOUT, count=1)

        shot.update()
        team.update()
        display.update()


# vim: et sw=4 sts=4
