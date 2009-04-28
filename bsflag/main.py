#!/usr/bin/env python

import os

DEFAULT_SIZE = 600, 600

IMG_DIR = '/usr/share/bzflag'
GROUND = 'std_ground.png'
BGSCALE = 0.1


def parse_args():
    import optparse
    p = optparse.OptionParser()
    p.add_option('--world', action='store', dest='world')
    return p.parse_args()


def run():
    opts, args = parse_args()
    print 'Loading.'

    from world import World
    if opts.world:
        f = open(opts.world)
        parser = World.parser()
        world = parser.parseString(f.read())
    else:
        world = World()


    import pygame

    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SIZE)
    screen.fill((255, 0, 0))
    pygame.display.flip()

    ground = pygame.image.load(os.path.join(IMG_DIR, GROUND)).convert()
    w, h = ground.get_size()
    w = int(w * BGSCALE)
    h = int(h * BGSCALE)
    print w, h

    scaled_ground = pygame.transform.smoothscale(ground, (w, h))
    bg = pygame.surface.Surface(screen.get_size())
    for i in xrange(screen.get_width() // w + 1):
        for j in xrange(screen.get_height() // h + 1):
            bg.blit(scaled_ground, (i * w, j * h))


    screen.blit(bg, (0, 0))
    pygame.display.flip()
    # Note that display.update(dirty_rects) can speed things up a lot.

    pygame.time.delay(20000)

# vim: et sw=4 sts=4
