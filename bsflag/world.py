"""World Model

We try to follow what BZFlag does.  The best resource is the man page for bzw.
"""

from pyparsing import alphas, nums, Word, Keyword
from pyparsing import Each, ZeroOrMore, Combine, Optional, Dict

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
point3d = floatnum + floatnum + floatnum

# hey!!!: pos is mandatory, but the others are optional!!!
obstacle_items = [
        Keyword('pos') | Keyword('position') + point3d,
        Optional(Keyword('size') + point3d),
        Optional(Keyword('rot') | Keyword('rotation') + point3d)]

box = Dict(Each(*obstacle_items))

base_items = [Keyword('color') + integer] + obstacle_items
base = Dict(Each(*base_items))

comment = '#' + SkipTo(LineEnd())

# For now, we're only supporting a subset of bzw's allobjects.
bzw = ZeroOrMore(box | base).ignore(comment)



class World(object):
    def __init__(self, bzw_string):


# vim: et sw=4 sts=4
