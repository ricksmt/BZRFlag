import sys, os
import optparse
import ConfigParser

import world

class ParseError(Exception):pass
class ArgumentError(Exception):pass

import logging
logger = logging.getLogger("config.py")

class Config:
    '''Config class:
    parses command line options and the --config file if given'''
    def __init__(self):
        self.options = self.parse_cli_args()
        self.setup_world()
        #logger.debug("Options:\n"+"\n".join("%s :: %s"%(k,v) for k,v in self.options.items()))

    def get(self, key, default):
        if self.options[key] is None:
            return default
        return self.options[key]

    def __getitem__(self, key):
        return self.options[key]

    def setup_world(self):
        if not self.options['world']:
            raise ArgumentError,'no world defined'
        if not os.path.isfile(self.options['world']):
            raise ArgumentError, 'world file not found: %s'%self.options['world']
        text = open(self.options['world']).read()
        parser = world.World.parser()
        results = world.World.parser().parseString(text)
        if not results:
            raise ParseError,'invalid world file: %s'%config['world']
        self.world = results[0]

    def parse_cli_args(self):
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
