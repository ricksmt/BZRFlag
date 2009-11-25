"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import asyncore
import os
import socket
import sys
import ConfigParser
import logging
logger = logging.getLogger('main')

import game
from game import Game
import server


def options():
    import optparse
    p = optparse.OptionParser()

    p.add_option('-d','--debug',
        action='store_true',
        dest='debug',
        help='set the debug level')

    ## world behavior
    p.add_option('--world',
        dest='world',
        help='specify a world.bzw map to use')
    p.add_option('--port',
        dest='port',default=3012,
        help='specify a port to use')
    ## changed name to config from 'bzrobots'...made sense
    p.add_option('--config',
        dest='config',
        help='set the config file')
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
            dest='%s_port'%color,type='int',
            help='specify the port for the %s team'%color)
        p.add_option('--%s-tanks'%color,
            dest='%s_tanks'%color,type='int',
            help='specify the number of tanks for the %s team'%color)
        p.add_option('--%s-posnoise'%color,
            dest='%s_posnoise'%color,
            help='specify the posnoise for the %s team'%color)
        p.add_option('--%s-velnoise'%color,
            dest='%s_velnoise'%color,
            help='specify the velnoise for the %s team'%color)
        p.add_option('--%s-angnoise'%color,
            dest='%s_angnoise'%color,
            help='specify the angnoise for the %s team'%color)

    opts, args = p.parse_args()

    if opts.config:
        configfile = ConfigParser.ConfigParser()
        if not len(configfile.read(opts.config)):
            raise Exception,'config file not found'
        if not 'global' in configfile.sections():
            raise Exception,'invalid config file. make sure "[global]"\
                             is at the top'
        config = dict(configfile.items('global'))

        for key in config:
            if not hasattr(opts,key):
                raise Exception,'invalid configuration option: %s'%key
            if getattr(opts,key) == None:
                type = p.get_option('--'+key.replace('_','-')).type
                value = config[key]
                if type == 'int':
                    value = int(value)
                setattr(opts,key,value)

    if args:
        p.parse_error('No positional arguments are allowed.')
    return vars(opts)

def run():
    config = options()

    from world import World
    if config['world']:
        f = open(config['world'])
        parser = World.parser()
        results = parser.parseString(f.read())
        world = results[0]
    else:
        world = World()

    #from bzrobots import BZRobots
    '''if opts.bzrobots:
        f = open(opts.bzrobots)
        parser = BZRobots.parser()
        results = parser.parseString(f.read())
        bzrobots = results[0]
    else:
        bzrobots = BZRobots()'''

    #colors = (1, 2)
    #colors = (1, 2, 3, 4)
    # Is world an appropriate parameter?
    game = Game(config, world)

    if not game.mapper.bases:
        raise Exception,'no bases defined -- include a world file?'
    if not game.mapper.teams:
        raise Exception,'no teams defined -- include a config file?'

    # Create a server for each team.
    # TODO: allow the port to be specified on the command-line.
    for team in game.mapper.teams:
        addr = ('0.0.0.0', team.port)
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
    world.display = display
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
