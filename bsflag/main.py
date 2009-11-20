"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import asyncore
import os
import socket
import sys

from game import *
import server


def options():
    import optparse
    p = optparse.OptionParser()
    # TODO: many of these options need to be implemented
    
    p.add_option('-d','--debug',
        action='store_true',
        dest='debug',
        help='set the debug level')
    
    ## world behavior
    p.add_option('--world',
        dest='world',
        help='specify a world.bzw map to use')
    p.add_option('--bzrobots',
        dest='bzrobots',
        help='set the bzrobots config file')
    p.add_option('--freeze-tag',
        action='store_true',
        dest='freeze_tag',
        help='start a freeze tag game')
    
    ## tank behavior
    p.add_option('--max-shots',
        type='int',
        dest='max_shots',
        help='set the max shots')
    p.add_option('--inertia-linear',
        dest='inertia_linear',
        type='int',default=1,
        help='set the linear inertia')
    p.add_option('--inertia-angular',
        dest='inertia_angular',
        type='int',default=1,
        help='set the angular inertia')
    p.add_option('--angular-velocity',
        type='float',
        dest='angular_velocity',
        help='set the angular velocity for tanks (float)')
    p.add_option('--rejoin-time',
        type='int',
        dest='rejoin_time',
        help='set the rejoin delay')
    p.add_option('--explode-time',
        type='int',
        dest='explode_time',
        help='[insert help] what does this do?')
    p.add_option('--grab-own-flag',
        action='store_false',
        dest='grab_own_flag',
        help='can you grab your own flag')
    
    for color in ['red','green','blue','purple']:
        p.add_option('--%s-port'%color,
            dest='%s_port'%color,
            help='specify the port for the %s team'%color)
    
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

    from bzrobots import BZRobots
    if opts.bzrobots:
        f = open(opts.bzrobots)
        parser = BZRobots.parser()
        results = parser.parseString(f.read())
        bzrobots = results[0]
    else:
        bzrobots = BZRobots()

    #colors = (1, 2)
    #colors = (1, 2, 3, 4)
    # Is world an appropriate parameter?
    game = Game(bzrobots, world)

    # Create a server for each team.	
    # TODO: allow the port to be specified on the command-line.
    for team in game.mapper.teams:
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

    #shotcount = 0
    #tankcount = 0

    for team in game.mapper.teams:
        #shotcount = shotcount + len(team.shots)
        for shot in team.shots:
            display.shot_sprite(shot)
        #tankcount = tankcount + len(team.tanks)
        for tank in team.tanks:
            display.tank_sprite(tank)
        display.flag_sprite(team.flag)

    game.loop(display)


# vim: et sw=4 sts=4
