'''Graphics module:
    handles all graphics; here are defined the base
classes for various graphics implementations to subclass

NOTE:
    to find the pygame implementation, look in modpygame.py

'''

import pygame
import constants
from world import Base, Box

DEFAULT_SIZE = 700, 700

DATA_DIR = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'data'))
GROUND = 'std_ground.png'
WALL = 'wall.png'
BASE_PATTERN = '%s_basetop.png'
SHOT_PATTERN = '%s_bolt.png'
FLAG_PATTERN = '%s_flag.png'
TANK_PATTERN = '%s_tank.png'
TILESCALE = 0.1
SHOTSCALE = 2
FLAGSCALE = 3
TANKSCALE = 1.2

class ImageCache(object):
    def __init__(self):
        self._ground = None
        self._wall = None

        self.suffixes = {'base':'basetop','shot':'bolt','tank':'tank','flag':'flag'}
        ## curently lazy loading...is that good?
        self._teamcache = {'base':{},'shot':{},'flag':{},'tank':{}}

    def ground(self):
        """Creates a surface of the ground image.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._cache.has_key('ground'):
            ground = load_image(GROUND)
            self._ground = scaled_image(ground, TILESCALE)
        return self._ground

    def wall(self):
        """Returns a surface for walls.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._wall:
            wall = load_image(WALL)
            self._wall = self.scaled_image(wall, TILESCALE)
        return self._wall

    def loadteam(self, type, color):
        if not self._teamcache.has_key(type):
            raise KeyError,"invalid image type: %s"%type
        if not color in constants.COLORS:
            raise KeyError,"invalid color: %s"%color
        if not self._teamcache[type].has_key(color):
            self._teamcache[type][color] = self.load_image('%s_%s.png'%(color,self.suffixes[type]))
        return self._teamcache[type][color]

    def scaled_size(self, size, scale):
        """Scales a size (width-height pair).

        If the scale is None, scaled_size returns the original size unmodified.
        """
        if scale is not None:
            w, h = size
            w = int(round(w * scale))
            h = int(round(h * scale))
            size = w, h
        return size

    def load_image(self, filename):
        """Loads the image with the given filename from the DATA_DIR."""
        raise Exception,'override this method'

    def scaled_image(self, image, scale):
        """Scales the given image to the given size."""
        raise Exception,'override this method'

    def tile(self, tile, size):
        """Creates a surface of the given size tiled with the given surface."""
        raise Exception,'override this method'

class Display(object):
    """Manages all graphics."""
    def __init__(self, world, screen_size=(700,700)):
        self.world = world
        self.screen_size = screen_size
        self.images = ImageCache()
        self._background = None

    def setup(self):
        """Initializes and creates the screen surface."""
        pass

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        pass

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

    def add_object(self, obj):
        types = (Tank, 'tank'),(Shot,'shot'),(Flag,'flag')
        otype = None
        for cls,name in types:
            if isinstance(obj,cls):
                otype = name
                break
        else:
            raise Exception,'invalid object added to display: %s'%obj

        image = self.images.loadteam(otype, obj.team.color)
        sprite = BZSprite(obj, image, self, 1)

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
        rot = 360 * self.bzobject.rot / (2 * math.pi)
        self.image = pygame.transform.rotate(self.image, rot)
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
            self.prev_rot = rot
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
            self.prev_rot = rot
            self.image = self.orig_image
            size = scaled_size(self.object_size(), self.scale)
            self.image = tile(self.image, size)
            self.rect.size = size
            if rot:
                self._rotate()

        self._translate()
