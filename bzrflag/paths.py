
import os

GROUND = 'std_ground.png'
WALL = 'wall.png'
FONT = 'VeraMono.ttf'
DATA_DIR = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'data'))
FONT_FILE = os.path.join(DATA_DIR, FONT)

# vim: et sw=4 sts=4
