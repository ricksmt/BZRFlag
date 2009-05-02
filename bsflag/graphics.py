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


def load_image(filename):
    """Loads the image with the given filename from the DATA_DIR.

    Note that convert_alpha is applied to the loaded image to preserve
    transparency.
    """
    path = os.path.join(DATA_DIR, filename)
    image = pygame.image.load(path).convert_alpha()
    return image


def scaled_image(image, scale):
    """Scales the given image to the given size."""
    w, h = image.get_size()
    w = int(w * scale)
    h = int(h * scale)

    return pygame.transform.smoothscale(image, (w, h))


def tile(tile, size):
    """Creates a surface of the given size tiled with the given surface."""
    tile_width, tile_height = tile.get_size()
    width, height = size
    surface = pygame.surface.Surface(size, pygame.SRCALPHA)
    for i in xrange(width // tile_width + 1):
        for j in xrange(height // tile_height + 1):
            surface.blit(tile, (i * tile_width, j * tile_height))
    return surface


class ImageCache(object):
    def __init__(self):
        self._ground = None
        self._wall = None
        self._bases = {}
        self._shots = {}
        self._tanks = {}

    def ground(self):
        """Creates a surface of the ground image.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._ground:
            ground = load_image(GROUND)
            self._ground = scaled_image(ground, TILESCALE)
        return self._ground

    def wall(self):
        """Returns a surface for walls.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._wall:
            wall = load_image(WALL)
            self._wall = scaled_image(wall, TILESCALE)
        return self._wall

    def base(self, color):
        """Returns a surface for the base for the given color index."""
        try:
            image = self._bases[color]
        except KeyError:
            image = load_image(BASE_PATTERN % COLOR_NAME[color])
            self._shots[color] = image
        return image

    def shot(self, color):
        """Returns a surface for shots for the given color index."""
        try:
            image = self._shots[color]
        except KeyError:
            image = load_image(SHOT_PATTERN % COLOR_NAME[color])
            self._shots[color] = image
        return image

    def tank(self, color):
        """Returns a surface for shots for the given color index."""
        try:
            image = self._tanks[color]
        except KeyError:
            image = load_image(TANK_PATTERN % COLOR_NAME[color])
            self._tanks[color] = image
        return image


class Display(object):
    """Manages all graphics."""
    def __init__(self, world, screen_size=DEFAULT_SIZE):
        self.world = world
        self.screen_size = screen_size
        self.screen = None
        self.sprites = None
        self.images = ImageCache()
        self._background = None

    def setup(self):
        """Initializes pygame and creates the screen surface."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_size)
        bg = self.background()
        self.screen.blit(bg, (0, 0))
        pygame.display.update()
        self.sprites = pygame.sprite.RenderUpdates()

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        self.sprites.update()
        bg = self.background()
        self.sprites.clear(self.screen, bg)
        changes = self.sprites.draw(self.screen)
        pygame.display.update(changes)

    def background(self):
        """Creates a surface of the background with all obstacles.

        Obstacles includes both bases and boxes.
        """
        if not self._background:
            bg = tile(self.images.ground(), self.screen_size)
            for box in self.world.boxes:
                s = TiledBZSprite(box, self.images.wall(), self)
                bg.blit(s.image, s.rect)
            for base in self.world.bases:
                image = self.images.base(base.color)
                s = BZSprite(base, image, self)
                bg.blit(s.image, s.rect)
            self._background = bg
        return self._background

    def tank_sprite(self, tank):
        """Creates a sprite for the given tank."""
        image = self.images.tank(tank.color)
        sprite = BZSprite(tank, image, self, TANKSCALE)
        self.sprites.add(sprite)

    def shot_sprite(self, shot):
        """Creates a sprite for the given shot."""
        image = self.images.shot(shot.color)
        sprite = BZSprite(shot, image, self, SHOTSCALE)
        self.sprites.add(sprite)

    def bzrect(self, bzobject, scale=None):
        """Returns a Rectangle for the given BZFlag object.

        The rectangle will be unrotated.
        """
        w, h = bzobject.size
        if scale:
            w *= scale
            h *= scale
        x, y = self.vec_world_to_screen((w, h))
        # Note that bzflag sizes are more like a radius (half of width).
        size = (2*x, -2*y)

        flat_pos = bzobject.pos
        pos = self.pos_world_to_screen(flat_pos)

        rect = pygame.Rect((0, 0), size)
        rect.center = pos
        return rect

    def pos_world_to_screen(self, pos):
        """Converts a position from world space to screen pixel space.

        >>> pos_world_to_screen((0, 0), (800, 800), (400, 400))
        (200, 200)
        >>> pos_world_to_screen((-400, -400), (800, 800), (400, 400))
        (0, 400)
        >>>
        """
        x, y = pos
        world_width, world_height = self.world.size
        x += world_width / 2
        y -= world_height / 2
        return self.vec_world_to_screen((x, y))

    def vec_world_to_screen(self, vector):
        """Converts a vector from world space to screen pixel space.

        >>> vec_world_to_screen((200, 200), (800, 800), (400, 400))
        (100, -100)
        >>>
        """
        screen_width, screen_height = self.screen_size
        world_width, world_height = self.world.size
        wscale = screen_width / world_width
        hscale = screen_height / world_height

        x, y = vector
        return int(x * wscale), -int(y * hscale)


class BZSprite(pygame.sprite.Sprite):
    def __init__(self, bzobject, image, display, scale=None):
        super(BZSprite, self).__init__()

        rect = display.bzrect(bzobject, scale)
        image = self.make_image(image, rect)

        if bzobject.rot:
            image = pygame.transform.rotate(image, bzobject.rot)
            rect.size = image.get_size()

        self.image = image
        self.rect = rect
        self.bzobject = bzobject
        self.display = display

    @staticmethod
    def make_image(image, rect):
        """Overrideable function for creating the image."""
        return pygame.transform.smoothscale(image, rect.size)

    def update(self):
        self.rect.center = self.display.pos_world_to_screen(self.bzobject.pos)


class TiledBZSprite(BZSprite):
    """An BZSprite with a tiled image."""
    @staticmethod
    def make_image(image, rect):
        return tile(image, rect.size)



if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
