#!/usr/bin/env python

DEFAULT_SIZE = 600, 600

def run():
    import pygame

    pygame.init()
    screen = pygame.display.set_mode(DEFAULT_SIZE)
    screen.fill((255, 0, 0))
    pygame.display.flip()

    import time
    time.sleep(4)

# vim: et sw=4 sts=4
