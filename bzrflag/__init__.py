'''
BZRFlag: BZFlag with Robots!
'''
import logging,os
LOG_FILENAME = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'debug.log'))
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

from main import run
