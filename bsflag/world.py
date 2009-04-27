"""World Model

We try to follow what BZFlag does.  The best resource is the man page for bzw.
"""

from pyparsing import alphas, nums, Word, Keyword, LineEnd
from pyparsing import Each, ZeroOrMore, Combine, Optional, Dict, SkipTo, Group

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

point2d = floatnum + floatnum
point2d.setName('point2d')
point3d = floatnum + floatnum + floatnum
point3d.setName('point3d')

# hey!!!: pos is mandatory, but the others are optional!!!
obstacle_items = [
        Group((Keyword('pos') | Keyword('position')) + point3d),
        Optional(Group(Keyword('size') + point3d)),
        Optional(Group((Keyword('rot') | Keyword('rotation')) + floatnum))]

box = Group(Keyword('box') + Dict(Each(obstacle_items)) + Keyword('end'))
box.setName('box').setDebug()

base_items = [Group(Keyword('color') + integer)] + obstacle_items
base = Group(Keyword('base') + Dict(Each(base_items)) + Keyword('end'))
base.setName('base').setDebug()

comment = '#' + SkipTo(LineEnd())

# For now, we're only supporting a subset of bzw's allobjects.
bzw = ZeroOrMore(box | base).ignore(comment)



class World(object):
    def __init__(self, bzw_string):
        tree = bzw.parseString(bzw_string)
        print tree


if __name__ == '__main__':
    f = open('maps/four_ls.bzw')
    w = World(f.read())

# vim: et sw=4 sts=4
