"""BZRFlag: BZFlag with Robots!

"""
import logging
import os

import config

LOG_FILENAME = os.path.abspath(os.path.join(
               os.path.split(__file__)[0], '..', 'debug.log'))


def run():
    """Run bzrflag game."""
    config.init()
    from game import Game # Cannot be imported befor config.init() is called!
    level = logging.WARNING
    if config.config['debug']:
        level = logging.DEBUG
    fname = config.config.get('debug_out', None)
    logging.basicConfig(level=level, filename=fname)
    g = Game()
    g.loop()
