#!/usr/bin/env python

from __future__ import division


DEFAULT_SIZE = 600, 600

IMG_DIR = '/usr/share/bzflag'
GROUND = 'std_ground.png'
BASE_PATTERN = '%s_basetop.png'
BGSCALE = 0.1

COLOR_NAME = dict(enumerate(('rogue', 'red', 'green', 'blue', 'purple')))

import os
import pygame
from world import Base


def make_screen():
    """Creates and returns the pygame screen surface."""
    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SIZE)
    return screen


def load_background(screen_size):
    """Creates a surface of the given size tiled with the background img."""
    filename = os.path.join(IMG_DIR, GROUND)
    ground = pygame.image.load(filename).convert()
    w, h = ground.get_size()
    w = int(w * BGSCALE)
    h = int(h * BGSCALE)

    scaled_ground = pygame.transform.smoothscale(ground, (w, h))
    bg = pygame.surface.Surface(screen_size)
    for i in xrange(screen_size[0] // w + 1):
        for j in xrange(screen_size[1] // h + 1):
            bg.blit(scaled_ground, (i * w, j * h))
    return bg


def load_base(color):
    """Returns a surface for the given color index."""
    filename = os.path.join(IMG_DIR, BASE_PATTERN % COLOR_NAME[color])
    image = pygame.image.load(filename).convert()
    return image


def draw_bases(world, surface):
    """Draws bases defined in the given world onto the given surface."""
    screen_size = surface.get_size()
    for item in world.items:
        if isinstance(item, Base):
            base = item
            image = load_base(base.color)

            # Note that bzflag sizes are more like a radius (half of width).
            flat_size = (2 * base.size[0]), (2 * base.size[1])
            size = vec_world_to_screen(flat_size, world.size, screen_size)
            scaled_image = pygame.transform.smoothscale(image, size)

            flat_pos = base.pos[0:2]
            corner_pos = pos_corner_from_center(flat_pos, flat_size)
            print corner_pos
            pos = pos_world_to_screen(corner_pos, world.size, screen_size)
            print pos

            surface.blit(scaled_image, pos)


def pos_corner_from_center(center, size):
    """Finds the corner of an object from its center and size.
    
    >>> pos_corner_from_center((0.0, 0.0), (800, 800))
    (-400.0, -400.0)
    >>>
    """
    x, y = center
    x -= size[0] / 2
    y -= size[1] / 2
    return x, y


def pos_world_to_screen(pos, world_size, screen_size):
    """Converts a position from world space to screen pixel space.
    
    >>> pos_world_to_screen((0, 0), (800, 800), (400, 400))
    (200, 200)
    >>>
    """
    x, y = pos
    world_width, world_height = world_size
    x += world_width / 2
    y += world_height / 2
    return vec_world_to_screen((x, y), world_size, screen_size)


def vec_world_to_screen(vector, world_size, screen_size):
    """Converts a vector from world space to screen pixel space.
    
    >>> vec_world_to_screen((200, 200), (800, 800), (400, 400))
    (100, 100)
    >>>
    """
    screen_width, screen_height = screen_size
    world_width, world_height = world_size
    wscale = screen_width / world_width
    hscale = screen_height / world_height

    x, y = vector
    return int(x * wscale), int(y * hscale)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4
