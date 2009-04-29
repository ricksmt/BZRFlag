#!/usr/bin/env python

from __future__ import division

DEFAULT_SIZE = 600, 600

IMG_DIR = '/usr/share/bzflag'
GROUND = 'std_ground.png'
WALL = 'wall.png'
BASE_PATTERN = '%s_basetop.png'
TILESCALE = 0.1

COLOR_NAME = dict(enumerate(('rogue', 'red', 'green', 'blue', 'purple')))

import os
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
    filename = os.path.join(IMG_DIR, GROUND)
    ground = pygame.image.load(filename).convert_alpha()
    scaled_ground = scaled_image(ground, scale)
    return tile(scaled_ground, screen_size)


def load_base(color):
    """Returns a surface for the given color index."""
    filename = os.path.join(IMG_DIR, BASE_PATTERN % COLOR_NAME[color])
    image = pygame.image.load(filename).convert_alpha()
    return image


def load_wall(scale=TILESCALE):
    """Returns a surface for walls."""
    filename = os.path.join(IMG_DIR, WALL)
    wall = pygame.image.load(filename).convert_alpha()
    return scaled_image(wall, scale)


def draw_obstacles(world, surface):
    """Draws obstacles defined in the given world onto the given surface.

    Obstacles includes both bases and boxes.
    """
    screen_size = surface.get_size()
    wall = load_wall()
    for item in world.items:
        if isinstance(item, Base):
            image = load_base(item.color)
            s = ObstacleSprite(item, image, world.size, screen_size)
        elif isinstance(item, Box):
            s = TiledObstacleSprite(item, wall, world.size, screen_size)
        else:
            print 'Warning: unknown obstacle.'
            continue

        surface.blit(s.image, s.rect)


def obstacle_rect(obstacle, world_size, screen_size):
    """Returns a Rectangle for the given BZFlag obstacle.

    The rectangle will be unrotated.
    """
    flat_size = obstacle.size[0:2]
    x, y = vec_world_to_screen(flat_size, world_size, screen_size)
    # Note that bzflag sizes are more like a radius (half of width).
    size = (2*x, -2*y)

    flat_pos = obstacle.pos[0:2]
    pos = pos_world_to_screen(flat_pos, world_size, screen_size)

    rect = pygame.Rect((0, 0), size)
    rect.center = pos
    return rect


class ObstacleSprite(pygame.sprite.Sprite):
    def __init__(self, obstacle, image, world_size, screen_size):
        super(ObstacleSprite, self).__init__()

        rect = obstacle_rect(obstacle, world_size, screen_size)
        image = self.make_image(image, rect)

        if obstacle.rot:
            image = pygame.transform.rotate(image, obstacle.rot)
            rect.size = image.get_size()

        self.image = image
        self.rect = rect
        self.obstacle = obstacle

    @staticmethod
    def make_image(image, rect):
        """Overrideable function for creating the image."""
        return pygame.transform.smoothscale(image, rect.size)


class TiledObstacleSprite(ObstacleSprite):
    """An ObstacleSprite with a tiled image."""
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
