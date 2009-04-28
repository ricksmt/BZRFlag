"""World Model

We try to follow what BZFlag does.  The best resource is the man page for bzw.
"""

from pyparsing import alphas, nums, Word, Keyword, LineEnd, \
        Each, ZeroOrMore, Combine, Optional, Dict, SkipTo, Group

def numeric(toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError:
        return float(n)

integer = Word(nums).setParseAction(numeric)

floatnum = Combine(
        Optional('-') + ('0' | Word('123456789',nums)) +
        Optional('.' + Word(nums)) +
        Optional(Word('eE',exact=1) + Word(nums+'+-',nums)))
floatnum.setParseAction(numeric)

end = Keyword('end').suppress()

point2d = floatnum + floatnum
point2d.setName('point2d')
point3d = floatnum + floatnum + floatnum
point3d.setName('point3d')

# Obstacle
position = Group((Keyword('pos') | Keyword('position')) + point3d)
size = Group(Keyword('size') + point3d)
rotation = Group((Keyword('rot') | Keyword('rotation')) + floatnum)
obstacle_items = [position, Optional(size), Optional(rotation)]


class Box(object):
    def __init__(self, pos=None, position=None, rot=None, rotation=None,
            size=None):
        self.pos = pos or position
        self.rot = rot or position
        self.size = size
        if not self.pos:
            raise ValueError('Position is required')

    @classmethod
    def parser(cls):
        box_contents = Each(obstacle_items)
        box = Dict(Keyword('box').suppress() + box_contents + end)
        box.setParseAction(lambda toks: cls(**toks))
        return box


class Base(object):
    def __init__(self, color=None, pos=None, position=None, rot=None,
            rotation=None, size=None):
        self.color = color
        self.pos = pos or position
        self.rot = rot or position
        self.size = size
        if self.color is None:
            raise ValueError('Color is required')
        if not self.pos:
            raise ValueError('Position is required')

    @classmethod
    def parser(cls):
        # Base
        color = Group(Keyword('color') + integer)
        base_contents = Each([color] + obstacle_items)
        base = Dict(Keyword('base').suppress() + base_contents + end)
        base.setParseAction(lambda toks: cls(**toks))
        return base


class World(list):
    @classmethod
    def parser(cls):
        """Parse a BZW file.

        For now, we're only supporting a subset of BZW's allobjects.
        """
        comment = '#' + SkipTo(LineEnd())
        bzw = ZeroOrMore(box.parser() | base.parser()).ignore(comment)
        bzw.setParseAction(lambda toks: cls(toks))
        return bzw


if __name__ == '__main__':
    f = open('maps/four_ls.bzw')
    parser = World.parser()
    w = parser.parseString(f.read())
    print w

# vim: et sw=4 sts=4
