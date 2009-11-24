"""BZ_2DFlag BZRobot Options

The BZ_2DFlag BZRobots module implements a parser for reading in config files.
"""

from __future__ import division

import math
from pyparsing import *

import logging
logger = logging.getLogger('bzrobots')

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

class Team(object):
    def __init__(self, color=None, tanks=None, rcport=None, p=None,
            hoverbot=None, posnoise=None, angnoise=None, velnoise=None):
        self.color = color
        self.tanks = tanks
        self.rcport = rcport or p
        self.hoverbot = hoverbot
        self.posnoise = posnoise
        self.angnoise = angnoise
        self.velnoise = velnoise
        if not self.color:
            raise ValueError('Color is required')

    @classmethod
    def parser(cls):
        # Team
        color = Group(Keyword('color') + integer)
        tanks = Group(Keyword('tanks') + integer)
        rcport = Group((Keyword('rcport') | Keyword('p')) + integer)
        hoverbot = Group(Keyword('hoverbot') + integer)
        posnoise = Group(Keyword('posnoise') + floatnum)
        angnoise = Group(Keyword('angnoise') + floatnum)
        velnoise = Group(Keyword('velnoise') + floatnum)
        team_items = [color, Optional(tanks), Optional(rcport),
            Optional(hoverbot), Optional(posnoise), Optional(angnoise),
            Optional(velnoise)]

        team_contents = Each(team_items)
        team = Dict(Keyword('team').suppress() + team_contents + end)
        team.setParseAction(lambda toks: cls(**dict(toks)))
        return team


class BZRobots(object):
    def __init__(self, items=None):
        self.teams = []
        if items:
            for item in items:
                if isinstance(item, Team):
                    self.teams.append(item)
                else:
                    raise NotImplementedError('Unhandled option element.')

    @classmethod
    def parser(cls):
        """Parse a BZR file.
        """
        comment = '#' + SkipTo(LineEnd())
        bzr = ZeroOrMore(Team.parser()).ignore(comment)
        bzr.setParseAction(lambda toks: cls(toks))
        return bzr


# vim: et sw=4 sts=4
