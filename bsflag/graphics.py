"""BSFlag Graphics Module

The graphics module encapsulates all of the little pieces needed to get things
to show up on the screen.  It uses pygame, a Python library built on top of
SDL (a cross-platform 2D graphics platform).  Anyway, BSFlag graphics includes
sprites and functions for transforming BZFlag coordinates to screen
coordinates.  Keep it simple.
"""

from __future__ import division
import os

DEFAULT_SIZE = 700, 700

DATA_DIR = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'data'))
GROUND = 'std_ground.png'
WALL = 'wall.png'
BASE_PATTERN = '%s_basetop.png'
SHOT_PATTERN = '%s_bolt.png'
TANK_PATTERN = '%s_tank.png'
TILESCALE = 0.1
SHOTSCALE = 8
TANKSCALE = 1.4

COLOR_NAME = dict(enumerate(('rogue', 'red', 'green', 'blue', 'purple')))

import pygame
from world import Base, Box


def make_screen():
    """Creates and returns the pygame screen surface."""
    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SIZE)
    return screen


def scaled_image(image, scale):
    """Scales the given image to the given size."""
    w, h = image.get_size()
    w = int(w * scale)
    h = int(h * scale)

    return pygame.transform.smoothscale(image, (w, h))


def load_background(screen_size, scale=TILESCALE):
    """Creates a surface of the given size tiled with the background img.

    The surface is scaled down according to the given scale factor.
    """
    filename = os.path.join(DATA_DIR, GROUND)
    ground = pygame.image.load(filename).convert_alpha()
    scaled_ground = scaled_image(ground, scale)
    return tile(scaled_ground, screen_size)


def load_base(color):
    """Returns a surface for the base for the given color index."""
    filename = os.path.join(DATA_DIR, BASE_PATTERN % COLOR_NAME[color])
    image = pygame.image.load(filename).convert_alpha()
    return image


def load_shot(color):
    """Returns a surface for shots for the given color index."""
    filename = os.path.join(DATA_DIR, SHOT_PATTERN % COLOR_NAME[color])
    image = pygame.image.load(filename).convert_alpha()
    return image


def load_tank(color):
    """Returns a surface for shots for the given color index."""
    filename = os.path.join(DATA_DIR, TANK_PATTERN % COLOR_NAME[color])
    image = pygame.image.load(filename).convert_alpha()
    return image


def load_wall(scale=TILESCALE):
    """Returns a surface for walls."""
    filename = os.path.join(DATA_DIR, WALL)
    wall = pygame.image.load(filename).convert_alpha()
    return scaled_image(wall, scale)


def draw_obstacles(world, surface):
    """Draws obstacles defined in the given world onto the given surface.

    Obstacles includes both bases and boxes.
    """
    screen_size = surface.get_size()
    wall = load_wall()
    for box in world.boxes:
        s = TiledBZSprite(box, wall, world.size, screen_size)
        surface.blit(s.image, s.rect)
    for base in world.bases:
        image = load_base(base.color)
        s = BZSprite(base, image, world.size, screen_size)
        surface.blit(s.image, s.rect)


def bzrect(bzobject, world_size, screen_size, scale=None):
    """Returns a Rectangle for the given BZFlag object.

    The rectangle will be unrotated.
    """
    w, h = bzobject.size
    if scale:
        w *= scale
        h *= scale
    x, y = vec_world_to_screen((w, h), world_size, screen_size)
    # Note that bzflag sizes are more like a radius (half of width).
    size = (2*x, -2*y)

    flat_pos = bzobject.pos
    pos = pos_world_to_screen(flat_pos, world_size, screen_size)

    rect = pygame.Rect((0, 0), size)
    rect.center = pos
    return rect


class BZSprite(pygame.sprite.Sprite):
    def __init__(self, bzobject, image, world_size, screen_size, scale=None):
        super(BZSprite, self).__init__()

        rect = bzrect(bzobject, world_size, screen_size, scale)
        image = self.make_image(image, rect)

        if bzobject.rot:
            image = pygame.transform.rotate(image, bzobject.rot)
            rect.size = image.get_size()

        self.image = image
        self.rect = rect
        self.bzobject = bzobject
        self.world_size = world_size
        self.screen_size = screen_size

    @staticmethod
    def make_image(image, rect):
        """Overrideable function for creating the image."""
        return pygame.transform.smoothscale(image, rect.size)

    def update(self):
        self.rect.center = pos_world_to_screen(self.bzobject.pos,
                self.world_size, self.screen_size)


class TiledBZSprite(BZSprite):
    """An BZSprite with a tiled image."""
    @staticmethod
    def make_image(image, rect):
        return tile(image, rect.size)


def tile(tile, size):
    """Creates a surface of the given size tiled with the given surface."""
    tile_width, tile_height = tile.get_size()
    width, height = size
    surface = pygame.surface.Surface(size, pygame.SRCALPHA)
    for i in xrange(width // tile_width + 1):
        for j in xrange(height // tile_height + 1):
            surface.blit(tile, (i * tile_width, j * tile_height))
    return surface


def pos_world_to_screen(pos, world_size, screen_size):
    """Converts a position from world space to screen pixel space.

    >>> pos_world_to_screen((0, 0), (800, 800), (400, 400))
    (200, 200)
    >>> pos_world_to_screen((-400, -400), (800, 800), (400, 400))
    (0, 400)
    >>>
    """
    x, y = pos
    world_width, world_height = world_size
    x += world_width / 2
    y -= world_height / 2
    return vec_world_to_screen((x, y), world_size, screen_size)


def vec_world_to_screen(vector, world_size, screen_size):
    """Converts a vector from world space to screen pixel space.

    >>> vec_world_to_screen((200, 200), (800, 800), (400, 400))
    (100, -100)
    >>>
    """
    screen_width, screen_height = screen_size
    world_width, world_height = world_size
    wscale = screen_width / world_width
    hscale = screen_height / world_height

    x, y = vector
    return int(x * wscale), -int(y * hscale)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
