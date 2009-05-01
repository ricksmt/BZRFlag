"""BSFlag Main

The BSFlag Main module contains the program's entry point and event loop.
"""

import constants


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
    screen_size = screen.get_size()
    bg = graphics.load_background(screen_size)
    graphics.draw_obstacles(world, bg)

    import pygame
    screen.blit(bg, (0, 0))
    pygame.display.update()

    group = pygame.sprite.RenderUpdates()

    shot = Shot()
    shot_image = graphics.load_shot(shot.color)
    shot_sprite = graphics.BZSprite(shot, shot_image, world.size, screen_size,
            graphics.SHOTSCALE)

    tank = Tank()
    tank_image = graphics.load_tank(tank.color)
    tank_sprite = graphics.BZSprite(tank, tank_image, world.size, screen_size,
            graphics.TANKSCALE)

    group.add(shot_sprite)
    group.add(tank_sprite)

    while True:
        shot.update()
        shot_sprite.update()
        tank.update()
        tank_sprite.update()

        group.clear(screen, bg)
        changes = group.draw(screen)
        pygame.display.update(changes)

        pygame.time.delay(100)


class Shot(object):
    color = 1
    size = (constants.ShotRadius,) * 2
    pos = (-400, 0)
    rot = None

    def update(self):
        x, y = self.pos
        self.pos = (x + 5), y


class Tank(object):
    color = 1
    size = (constants.TankRadius,) * 2
    pos = (-400, 200)
    rot = None

    def update(self):
        x, y = self.pos
        self.pos = (x + 5), y


# vim: et sw=4 sts=4
