"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import asyncore
import os
import socket
import sys

from game import Game
import server

# A higher loop timeout decreases CPU usage but also decreases the frame rate.
LOOP_TIMEOUT = 0.01


def options():
    import optparse
    p = optparse.OptionParser()
    # TODO: many of these options need to be implemented
    p.add_option('-c', action='store_true', dest='ctf')
    p.add_option('-d', action='store_true', dest='debug')
    p.add_option('--ms', action='store', type='int', dest='max_shots',
        default=6)
    p.add_option('--freezeTag', action='store_true', dest='freeze_tag')
    p.add_option('--world', action='store', dest='world')
    p.add_option('--set_inertiaLinear', action='store', type='int',
        dest='inertia_linear', default=1)
    p.add_option('--set_inertiaAngular', action='store', type='int', 
        dest='inertia_angular', default=1)
    p.add_option('--set_tankAngVel', action='store', type='float',
        dest='tank_angvel')
    p.add_option('--set_rejoinTime', action='store', type='int',
        dest='rejoin_time')
    p.add_option('--set_explodeTime', action='store', type='int',
        dest='explode_time')
    p.add_option('--set_grabOwnFlag', action='store', type='int',
        dest='grab_own_flag', default=0)
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

    colors = (1, 2)
    # Is world an appropriate parameter?
    game = Game(colors, world)

    # Create a server for each team.
    # TODO: allow the port to be specified on the command-line.
    for team in game.teams:
        addr = ('0.0.0.0', opts.port)
        try:
            bzrc = server.Server(addr, team)
        except socket.error, e:
            print >>sys.stderr, 'Socket error:', os.strerror(e.errno)
            sys.exit(1)
        host, port = bzrc.socket.getsockname()
        print 'Listening on port %s for %s team.' % (port, team.color_name())


    import graphics
    display = graphics.Display(world)
    display.setup()

    shotcount = 0
    tankcount = 0

    for team in game.teams:
        shotcount = shotcount + len(team.shots)
        for shot in team.shots:
            display.shot_sprite(shot)
        tankcount = tankcount + len(team.tanks)
        for tank in team.tanks:
            display.tank_sprite(tank)
        display.flag_sprite(team.flag)

    while True:
        asyncore.loop(LOOP_TIMEOUT, count=1)

        # TODO: clean this up
        shottemp = 0
        tanktemp = 0

        for team in game.teams:
            shottemp = shottemp + len(team.shots)
            tanktemp = tanktemp + len(team.tanks)

        if shottemp > shotcount:
            for team in game.teams:
                for shot in team.shots:
                    display.shot_sprite(shot)
        if tanktemp > tankcount:
            for team in game.teams:
                for tank in team.tanks:
                    display.tank_sprite(tank)


        game.update()
        display.update()


# vim: et sw=4 sts=4
