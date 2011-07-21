#!/usr/bin/env python
# Bzrflag
# Copyright 2008-2011 Brigham Young University
#
# This file is part of Bzrflag.
#
# Bzrflag is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Bzrflag is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Bzrflag.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of Bzrflag, please contact the Copyright
# Licensing Office, Brigham Young University, 3760 HBLL, Provo, UT 84602,
# (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

"""2D collision testing for BZRFlag game.

point : (x,y)
line : ((x1,y1),(x2,y2))
circle : ((cx,cy),r)
rectangle : (x,y,w,h)
polygon : ((x1,y1),(x2,y2),(x3,y3)...)

"""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import math
import logging

logger = logging.getLogger('collisiontest.py')


def point_in_rect(point, rect):
    """Check if point falls in given rectangle.
        
    @return: True/False
    
    >>> rect = (2,3,2,2)
    >>> point_in_rect((3,4), rect)
    True
    >>> point_in_rect((1,2), rect)
    False
    """
    (x, y, w, h) = rect
    poly = ((x,y), (x,y+h), (x+w,y+h), (x+w,y))
    return point_in_poly(point, poly)
    
    
def point_in_poly(point, poly):
    """Check if point falls in given polygon.
        
    @return: True/False
    
    >>> poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0, 5))
    >>> point_in_poly((.5,1), poly)
    True
    >>> point_in_poly((5,2), poly)
    False
    >>> point_in_poly((2,2), poly)
    True
    >>> point_in_poly((0,5), poly)
    False
    """
    n = len(poly)
    inside = False
    (x, y) = point

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside
    

def line_cross_rect(line, rect):
    """Check if line crosses or falls in given rectangle.
        
    @return: True/False
    """
    pass
    
    
def line_cross_circle(line, circle):
    """Check if line crosses or falls in given circle.
        
    @return: True/False
    """
    pass


def circle_to_rect(circle, rect):
    """Check if circle overlaps or falls in given rectangle.
        
    @return: True/False
    """
    pass
    
    
def circle_to_circle(circle1, circle2):
    """Check if circle1 overlaps or falls in circle2.
        
    @return: True/False
    """
    pass
    
     
def circle_to_poly(circle, poly):
    """Check if circle overlaps or falls in given polygon.
        
    @return: True/False
    """
    pass
    
    
def get_dist(point1, point2):
    """Calculate distance between point1 and point2.
        
    @return: Pythagorean distance between points.
    
    >>> get_dist((0,0), (4,3))
    5.0
    """
    (x1,y1) = point1
    (x2,y2) = point2
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
            
if __name__=='__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4

