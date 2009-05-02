"""BSFlag Graphics Module

The graphics module encapsulates all of the little pieces needed to get things
to show up on the screen.  It uses pygame, a Python library built on top of
SDL (a cross-platform 2D graphics platform).  Anyway, BSFlag graphics includes
sprites and functions for transforming BZFlag coordinates to screen
coordinates.  Keep it simple.
"""

from __future__ import division
import math
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
SHOTSCALE = 2
TANKSCALE = 1.2

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


def scaled_size(size, scale):
    """Scales a size (width-height pair).

    If the scale is None, scaled_size returns the original size unmodified.
    """
    if scale is not None:
        w, h = size
        w = int(round(w * scale))
        h = int(round(h * scale))
        size = w, h
    return size


def scaled_image(image, scale):
    """Scales the given image to the given size."""
    size = scaled_size(image.get_size(), scale)
    return pygame.transform.smoothscale(image, size)


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

    def size_world_to_screen(self, size):
        """Converts sizes from BZFlag world space to screen space.

        Note that bzflag sizes are more like a radius (half of width), so we
        double them to normalize.
        """
        w, h = size
        w *= 2
        h *= -2
        screen_size = self.vec_world_to_screen((w, h))
        return screen_size

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
        return int(round(x * wscale)), -int(round(y * hscale))


class BZSprite(pygame.sprite.Sprite):
    """Determines how a single object in the game will be drawn.

    The sprite manager uses the sprite's `image` and `rect` attributes to draw
    it.
    """

    def __init__(self, bzobject, image, display, scale=None):
        super(BZSprite, self).__init__()

        self.bzobject = bzobject
        self.display = display
        self.orig_image = image
        self.image = None
        self.scale = scale

        #self.rect = display.bzrect(bzobject, scale)
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.prev_rot = None

        self.update(True)

    def object_size(self):
        """Finds the screen size of the original unrotated bzobject."""
        return self.display.size_world_to_screen(self.bzobject.size)

    def _rotate(self):
        """Rotates the image according to the bzobject.

        Don't rotate a previously rotated object.  That causes data loss.
        """
        self.image = pygame.transform.rotate(self.image, self.bzobject.rot)
        self.rect.size = self.image.get_size()

    def _scale_prerotated(self):
        """Scales the image to the bzobject's prerotated size."""
        size = scaled_size(self.object_size(), self.scale)
        self.image = pygame.transform.smoothscale(self.image, size)
        self.rect.size = size

    def _scale_rotated(self):
        """Scales the image to the bzobject's rotated size."""
        rot = self.bzobject.rot
        w, h = self.object_size()
        new_w = abs(w * math.cos(rot)) + abs(h * math.sin(rot))
        new_h = abs(h * math.cos(rot)) + abs(w * math.sin(rot))
        size = scaled_size((new_w, new_h), self.scale)

        self.image = pygame.transform.smoothscale(self.image, size)
        self.rect.size = size

    def _translate(self):
        """Translates the image to the bzobject's position."""

        self.rect.center = self.display.pos_world_to_screen(self.bzobject.pos)

    def update(self, force=False):
        """Overrideable function for creating the image.

        If force is specified, the image should be redrawn even if the
        bzobject doesn't appear to have changed.
        """
        rot = self.bzobject.rot

        if force or (rot != self.prev_rot):
            self.image = self.orig_image
            if rot:
                self._rotate()
                self._scale_rotated()
            else:
                self._scale_prerotated()

        self._translate()


class TiledBZSprite(BZSprite):
    """A BZSprite with a tiled image."""

    def update(self, force=False):
        rot = self.bzobject.rot

        if force or (rot != self.prev_rot):
            self.image = self.orig_image
            size = scaled_size(self.object_size(), self.scale)
            self.image = tile(self.image, size)
            self.rect.size = size
            if rot:
                self._rotate()

        self._translate()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
