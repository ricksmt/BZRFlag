import os
import pygame
from pygame.locals import *

import graphics
import constants

DEFAULT_SIZE = 700, 700

DATA_DIR = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'data'))
GROUND = 'std_ground.png'
WALL = 'wall.png'

class ImageCache(graphics.ImageCache):
    def load_image(self, filename):
        path = os.path.join(DATA_DIR, filename)
        image = pygame.image.load(path).convert_alpha()
        return image

    def scaled_image(self, image, scale):
        size = self.scaled_size(image.get_size(), scale)
        return pygame.transform.smoothscale(image, size)

    def tile(self, tile, size):
        tile_width, tile_height = tile.get_size()
        width, height = size
        surface = pygame.surface.Surface(size, pygame.SRCALPHA)
        for i in xrange(width // tile_width + 1):
            for j in xrange(height // tile_height + 1):
                surface.blit(tile, (i * tile_width, j * tile_height))
        return surface

class Display(graphics.Display):
    _imagecache = ImageCache
    def setup(self):
        """Initializes pygame and creates the screen surface."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_size)
        #self.log = LogSprite(self, (0, self.screen_size[1]-200, self.screen_size[0], 200))
        bg = self.background()
        self.screen.blit(bg, (0, 0))
        pygame.display.update()
        self.sprites = pygame.sprite.RenderUpdates()
        #self.sprites.add(self.log)

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        self.sprites.update()
        bg = self.background()
        self.sprites.clear(self.screen, bg)
        changes = self.sprites.draw(self.screen)
        pygame.display.update(changes)
        for e in pygame.event.get():
            if e.type == QUIT:
                self.game.running = False
                self.game.map.end_game = True
            else:
                pass#pygame.event.post(e)

    def background(self):
        """Creates a surface of the background with all obstacles.

        Obstacles includes both bases and boxes.
        """
        if not self._background:
            bg = self.images.tile(self.images.ground(), self.screen_size)
            for box in self.world.boxes:
                s = graphics.TiledBZSprite(box, self.images.wall(), self)
                bg.blit(s.image, s.rect)
            for base in self.world.bases:
                image = self.images.loadteam('base',base.color)
                s = graphics.BZSprite(base, image, self)
                bg.blit(s.image, s.rect)
            self._background = bg
        return self._background
