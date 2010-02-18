import os
import pygame
from pygame.locals import *

import graphics
import constants
import math

import pygameconsole

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

    def rotate(self, image, rot):
        nimg = pygame.transform.rotate(image, rot/math.pi*180)
        return nimg

    def tile(self, tile, size):
        tile_width, tile_height = tile.get_size()
        width, height = size
        surface = pygame.surface.Surface(size, pygame.SRCALPHA)
        for i in xrange(width // tile_width + 1):
            for j in xrange(height // tile_height + 1):
                surface.blit(tile, (i * tile_width, j * tile_height))
        return surface

class BZSprite(graphics.BZSprite):

    def _render_image(self):
        if self.display.scale == self.prev_scale and self.bzobject.rot == self.prev_rot:
            return

        image = self._rotate_image(self.orig_image, self.bzobject.rot * 180/math.pi)
        if self.type == 'shot':
            comp = 3
        elif self.type == 'flag':
            comp = 4
        else:
            comp = 1
        wscale = self.display.world_to_screen_scale()
        isize = image.get_rect().size
        obj_size = wscale[0]*self.bzobject.size[0], wscale[1]*self.bzobject.size[1]
        orig_size = self.orig_image.get_rect().size
        thescale = [obj_size[0]/orig_size[0] *comp, obj_size[1]/orig_size[1]*comp]
        image = self._rescale_image(image,thescale)

        self.prev_scale = self.display.scale
        self.prev_rot = self.bzobject.rot
        self.image = image

    def _scale_image(self, image, scale):
        size = image.get_rect().size
        nsize = self.display.images.scaled_size(size, scale)
        return pygame.transform.smoothscale(image,nsize)

    def _rescale_image(self, image, scale):
        size = image.get_rect().size
        return pygame.transform.smoothscale(image,(size[0]*scale[0], size[1]*scale[1]))

    def _rotate_image(self, image, rotation):
        return pygame.transform.rotate(image, rotation)

class TiledBZSprite(BZSprite):
    """A BZSprite with a tiled image."""

    def _render_image(self):

        self.prev_rot = self.bzobject.rot
        image = self.orig_image
        image = self.display.images.tile(image, self.bzobject.size)
        image = self.display.images.rotate(image, self.bzobject.rot)
        self.image = image
        self._translate()

class TextSprite(graphics.TextSprite):

    def refresh(self):
        self.text = self.bzobject.text()
        lines = self.text.split('\n')
        font = pygame.font.Font(None, 25)
        mw = 0
        mh = 0
        for line in lines:
            w,h = font.size(line)
            if w>mw:mw=w
            mh += h
        image = pygame.Surface((mw,mh))
        at = 0
        for line in lines:
            image.blit(font.render(line, False, (255, 255, 255)), (0,at))
        self.image = image
        image.set_colorkey((0,0,0))
        self.rect.size = image.get_rect().size

    def reposition(self):
        self.rect.center = (0,0)#self.display.pos_world_to_screen(self.bzobject.pos)

class Display(graphics.Display):
    _imagecache = ImageCache
    _spriteclass = BZSprite
    _textclass = TextSprite
    
    def setup(self):
        """Initializes pygame and creates the screen surface."""
        pygame.init()
        pygame.key.set_repeat(50,50)
        self.screen = pygame.display.set_mode(self.screen_size)
        self._screen = pygame.Surface(self.screen_size)
        bg = self.background()
        self.screen.blit(bg, (0, 0))
        pygame.display.update()
        self.sprites = pygame.sprite.LayeredUpdates()
        self.console = pygameconsole.Console(self.game, (25,self.screen_size[1]*2/3-25,self.screen_size[0]-50,self.screen_size[1]/3))

    def add_sprite(self, sprite, otype):
        self.sprites.add(sprite,layer = ['base','tank','flag','shot','score'].index(otype))

    def remove_sprite(self, sprite):
        self.sprites.remove(sprite)

    def process_events(self):
        dirty = False
        for e in pygame.event.get():
            self.console.event(e)
            if e.type == QUIT:
                self.game.running = False
                self.game.map.end_game = True
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == 4:
                    dirty = True
                    self.rescale(self.scale*1.1, e.pos)
                elif e.button == 5:
                    self.rescale(self.scale*(1/1.1), e.pos)
                    dirty = True
            elif e.type == KEYDOWN:
                amt = 20
                if not self.console.minimized:
                    continue
                if e.key == K_DOWN:
                    self.pos[1] -= amt
                elif e.key == K_UP:
                    self.pos[1] += amt
                elif e.key == K_LEFT:
                    self.pos[0] += amt
                elif e.key == K_RIGHT:
                    self.pos[0] -= amt
                else:
                    continue
                dirty = True
            elif e.type == MOUSEMOTION:
                if e.buttons[0]:
                    self.pos[0]+=e.rel[0]
                    self.pos[1]+=e.rel[1]
                    dirty = True
        if dirty:
            self.redraw()

    def rescale(self, scale, pos):
        if scale < 1:return False
        if scale > 20:
            return False
        oscale = self.scale
        self.scale = scale


        realpos = (pos[0] - self.pos[0])/oscale, (pos[1] - self.pos[1])/oscale
        #realpos = (pos[0] - self.pos[0])/self.scale
        self.pos[0] = pos[0] - realpos[0]*self.scale
        self.pos[1] = pos[1] - realpos[1]*self.scale

        #self.pos[0] -= scale * pos[0] - oscale * pos[0]
        #self.pos[1] -= scale * pos[1] - oscale * pos[1]
        #self.redraw()

    def redraw(self):
        size = self._normal_background.get_rect().size
        if self.pos[0]>0:self.pos[0] = 0
        if self.pos[1]>0:self.pos[1] = 0
        if self.pos[0]<self.screen_size[0] - size[0]*self.scale:
            self.pos[0] = self.screen_size[0] - size[0]*self.scale
        if self.pos[1]<self.screen_size[1] - size[1]*self.scale:
            self.pos[1] = self.screen_size[1] - size[1]*self.scale
        ## problem: jerky background.
        tmp = pygame.Surface((size[0]/self.scale,size[1]/self.scale))
        tmp.blit(self._normal_background, (self.pos[0]/self.scale-1, self.pos[1]/self.scale-1))

        self._background = pygame.transform.smoothscale(tmp, size)
        self.screen.blit(self._background,(0,0))
        self.sprites.update()
        for layer in self.sprites.layers():
            for sprite in self.sprites.get_sprites_from_layer(layer):
                self.screen.blit(sprite.image,sprite.rect)
        self.console.draw(self.screen)
        pygame.display.flip()

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        self.sprites.update()
        bg = self.background()
        #self.sprites.clear(self.screen, bg)
        #changes = self.sprites.draw(self.screen)
        self.screen.blit(self.background(),(0,0))
        self.sprites.draw(self.screen)
        ## add a check for pygame input later
        self.process_events()
        #pygame.display.update(changes)
        self.console.draw(self.screen)
        self.scores.draw(self.screen)
        pygame.display.flip()

    def background(self):
        """Creates a surface of the background with all obstacles.

        Obstacles includes both bases and boxes.
        """
        if not self._background:
            wscale = self.world_to_screen_scale()
            bg = self.images.tile(self.images.ground(), self.screen_size)
            for box in self.game.map.obstacles:
                s = TiledBZSprite(box, self.images.wall(), self)
                bg.blit(s.image, s.rect.topleft)
                #print box.shape
                #pts = list(self.pos_world_to_screen(xy) for xy in box.shape)
                #pygame.draw.lines(bg, (255,255,255), 1, pts, 4)
            self._normal_background = self._background = bg
        return self._background

