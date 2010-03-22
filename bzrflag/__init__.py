'''
BZRFlag: BZFlag with Robots!
'''
import logging,os
LOG_FILENAME = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'debug.log'))

#from main import run
import config

def run():
    config.init()
    from game import Game
    level = logging.CRITICAL
    if config.config['debug']:
        level = logging.DEBUG
    fname = config.config.get('debug_out', None)
    logging.basicConfig(level=level, filename=fname)
    g = Game()
    g.loop()
