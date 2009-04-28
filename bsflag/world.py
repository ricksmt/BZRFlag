"""World Model

We try to follow what BZFlag does.  The best resource is the man page for bzw.
"""


def numeric(toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError:
        return float(n)


class World(object):
    def __init__(self, bzw_string):
        tree = bzw.parseString(bzw_string)
        print tree

    @classmethod
    def parser(cls):
        from pyparsing import alphas, nums, Word, Keyword, LineEnd, \
                Each, ZeroOrMore, Combine, Optional, Dict, SkipTo, Group
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
        position = Group((Keyword('pos') | Keyword('position')) + point3d)
        size = Group(Keyword('size') + point3d)
        rotation = Group((Keyword('rot') | Keyword('rotation')) + floatnum)
        obstacle_items = [position, Optional(size), Optional(rotation)]

        box_contents = Dict(Each(obstacle_items))
        box = Group(Keyword('box') + box_contents + Keyword('end'))

        color = Group(Keyword('color') + integer)
        base_contents = Dict(Each([color] + obstacle_items))
        base = Group(Keyword('base') + base_contents + Keyword('end'))

        comment = '#' + SkipTo(LineEnd())

        # For now, we're only supporting a subset of bzw's allobjects.
        bzw = ZeroOrMore(box | base).ignore(comment)
        return bzw


if __name__ == '__main__':
    f = open('maps/four_ls.bzw')
    parser = World.parser()
    w = parser.parseString(f.read())
    print w

# vim: et sw=4 sts=4
