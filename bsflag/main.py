#!/usr/bin/env python


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
        results = parser.parseString(f.read())
        world = results[0]
    else:
        world = World()

    import graphics

    screen = graphics.make_screen()
    bg = graphics.load_background(screen.get_size())
    graphics.draw_bases(world, bg)

    import pygame
    screen.blit(bg, (0, 0))
    pygame.display.flip()
    # Note that display.update(dirty_rects) can speed things up a lot.

    pygame.time.delay(20000)

# vim: et sw=4 sts=4
