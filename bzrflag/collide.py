'''
collide.py
Jared Forsyth (jabapyth)
This is a lightweight library implementing collision testing
of a 2D Plane. Feel free to just copy/paste one functon, or
use the whole library, but please credit me in a comment.

(object):(form)

point : (x,y)
line : ((x1,y1),(x2,y2))
circle : ((cx,cy),r)
rect : (x,y,w,h)
polygon : ((x1,y1),(x2,y2),(x3,y3)...)

note: in the function name, the more complex object comes first.

collision functions defined:

line2point(line,point)
line2line(line,line)

circle2point(circle,point)
circle2line(circle,line)
circle2circle(circle,circle)

rect2point(rect,point)
rect2line(rect,line)
rect2rect(rect,rect)

poly2line(poly,line)
poly2circle(coply,circle)
poly2poly(poly,poly)

'''
import math
#import scipy
#from scipy.weave import converters
#from scipy import weave

import logging
logger = logging.getLogger('collide.py')

'''
line2line proof:

y=mx+b
y-y1 = m(x-x1)
y-y1 = ((y2-y1)/(x2-x1))(x-x1)
m1 = ((y2-y1)/(x2-x1))
y = ((y2-y1)/(x2-x1))(x-x1)+y1

y-b1 = ((b2-b1)/(a2-a1))(x-a1)
m2 = ((b2-b1)/(a2-a1))
y = ((b2-b1)/(a2-a1))(x-a1)+b1
y = m2(x-a1)+b1

## eliminate the "y"
((y2-y1)/(x2-x1))(*x*-x1)+y1 = ((b2-b1)/(a2-a1))(*x*-a1)+b1
((y2-y1)/(x2-x1))(*x*-x1)-((b2-b1)/(a2-a1))(*x*-a1)  =  b1-y1

m1(*x*-x1)+y1 = m2(*x*-a1)+b1
m1(*x*-x1)-m2(*x*-a1)  =  b1-y1
m1x-m1x1-m2x+m2a1 = b1-y1
m1x - m2x = b1-y1+m1x1-m2a1
x(m1-m2) = b1-y1+m1x1-m2a1

#final equation
x = (b1-y1+m1x1-m2a1)/(m1-m2)
# got x, plug into first equ
y = m1(x-x1)+y1
'''

def line2point(line, point):
    '''find whether a point is on a line:
    @param: line
    @param: point

    @returns: True/False

    >>> line2point(((0,0),(4,4)),(1,1))
    (1, 1)
    >>> line2point(((0,0),(4,4)),(0,1))
    False
    >>> line2point(((1,1),(4,1)),(2,1))
    (2, 1)
    >>> line2point(((2,2),(2,6)),(2,5))
    (2, 5)
    >>> line2point(((2,2),(2,6)),(1,6))
    False
    >>> line2point(((2,2),(2,6)),(2,2))
    (2, 2)
    '''
    ((x1,y1),(x2,y2)) = line
    (x,y) = point
    if (x1==x2):
        return x==x1 and y1<=y<=y2 and (x,y)
    m = (y2-y1)/(x2-x1)
    # y - y1 = m(x-x1)
    online =  y - y1 == m*(x-x1)
    return online and rect2point((x1,y1,x2-x1,y2-y1),(x,y)) and (x,y)

def line2line(line1, line2):
    '''find where two lines intersect
    @param: line1
    @param: line2

    @return: the point of intersection or False if there is none

    >>> line2line(((0,0),(2,2)),((2,0),(0,2)))
    (1, 1)
    >>> line2line(((1,1),(3,5)),((1,4),(3,2)))
    (2, 3)
    >>> line2line(((1,1),(3,5)),((3,0),(3,6)))
    (3, 5)
    >>> line2line(((1,1),(3,5)),((0,5),(4,5)))
    (3, 5)
    >>> line2line(((0,0),(0,2)),((1,0),(1,2)))
    False
    >>> line2line(((0,0),(1,1)),((0,0),(1,1)))
    (0.5, 0.5)
    >>> line2line(((1,2),(3,2)),((2,1),(2,3)))
    (2, 2)
    '''
    ((x1,y1),(x2,y2)) = line1
    ((a1,b1),(a2,b2)) = line2

    if x2==x1:
        if a2 == a1:
            if x1 == a1:
                return (x1,y1)
            else:
                return False
        x=x1
        m1 = (b2-b1)/float(a2-a1)
    elif a2==a1:
        x=a1
        m1 = (y2-y1)/float(x2-x1)
    else:
        m1 = (y2-y1)/float(x2-x1)
        m2 = (b2-b1)/float(a2-a1)
        if m1==m2:
            ## check to see if they are the same line
            _b1 = m1*(x1) - y1
            _b2 = m2*(a1) - b1
            if _b1 == _b2: # on the same line
                return rectcenter(rectunion((x1,y1,x2-x1,y2-y1),(a1,b1,a2-a1,b2-b1)))
            return False
        x = round((m1*x1-m2*a1+b1-y1)/float(m1-m2),5)
    y = round(m1*(x-x1)+y1,5)
    return (rect2point((x1,y1,x2-x1,y2-y1),(x,y)) and rect2point((a1,b1,a2-a1,b2-b1),(x,y))) and (int(round(x)),int(round(y)))

def rectunion(rect1,rect2):
    '''TODO: move to a utils module
    @param: rect1
    @param: rect2

    @return: unified_rect

    >>> rectunion((0,0,10,10),(5,5,10,10))
    (0, 0, 15, 15)
    '''
    pts = _rect2pts(rect1) + _rect2pts(rect2)
    x = min(p[0] for p in pts)
    y = min(p[1] for p in pts)
    r = max(p[0] for p in pts)
    b = max(p[1] for p in pts)
    return x, y, r-x, b-y

def rectcenter(rect):
    '''find the center of a rectangle
    >>> rectcenter((0,0,10,4))
    (5.0, 2.0)
    >>> rectcenter((0,2,3,4))
    (1.5, 4.0)
    '''
    (a,b,c,d) = rect
    return a+c/2.0, b+d/2.0

def circle2point(circle, point):
    '''test if a point is inside a circle
    >>> circle2point(((0,0),3),(0,0))
    (0, 0)
    >>> circle2point(((0,0),3),(1,0))
    (1, 0)
    >>> circle2point(((0,0),3),(2,1))
    (2, 1)
    >>> circle2point(((0,0),3),(3,1))
    False
    >>> circle2point(((5,1),2),(5,2))
    (5, 2)
    '''
    return dist(circle[0], point)<=circle[1] and point

def circle2line(circle, line):
    '''test if a line collides or is inside a circle
    >>> c = ((3,4),4)
    >>> circle2line(c, ((3,4),(10,23)))
    (3, 4)
    >>> circle2line(c, ((0,0),(-1,-1)))
    False
    >>> circle2line(c, ((0,0),(0,6)))
    (0, 4)
    '''
    d,pos = dist_to_line(circle[0], line)
    if d>circle[1]:
        return False
    x,y = line[0]
    a,b = line[1]
    if rect2point((x,y,a-x,b-y),pos):
        return pos
    return circle2point(circle, line[0]) or circle2point(circle, line[1])

def circle2circle(circle1, circle2):
    '''test if two circles intersect
    >>> circle2circle(((0,0),3), ((4,0),1))
    True
    >>> circle2circle(((0,0),3), ((4.1,0),1))
    False
    '''
    return dist(circle1[0], circle2[0]) <= circle1[1] + circle2[1]

def rect2point(rect, point):
    '''test for a collision from a rectangle to a point
    >>> rect2point((1,2,4,5),(2,3))
    True
    >>> rect2point((0,0,3,4),(6,7))
    False
    '''
    (x,y,w,h) = rect
    (x1,y1) = point
    if w<0:
        x+=w
        w*=-1
    if h<0:
        y+=h
        h*=-1
    return x<=x1<=x+w and y<=y1<=y+h

def rect2line(rect, line):
    '''find if a rect intersects with a line
    >>> rect2line((2,3,4,5),((0,0),(9,9)))
    True
    >>> rect2line((0,0,3,4),((-1,0),(-1,5)))
    False
    '''
    ## TODO: design a function for if a line is *inside* a polygon
    return poly2line(_rect2pts(rect), line)

def rect2rect(rect1,rect2):
    '''collide two rectangles
    >>> rect2rect((0,0,3,4),(1,1,5,6))
    True
    >>> rect2rect((0,1,7,8),(10,10,3,4))
    False
    '''
    for point in _rect2pts(rect1):
        if rect2point(rect2, point):
            return True
    return False

#    return poly2poly(_rect2pts(rect1),_rect2pts(rect2))

def rect2circle(rect,circle):
    '''collide a rect and a circle
    >>> rect2circle((0,0,4,5), ((2,2),1))
    True
    >>> rect2circle((1,1,5,4), ((6,6),3))
    True
    >>> rect2circle((0,0,3,3), ((5,5),1))
    False
    '''
    return rect2point(rect, circle[0]) or poly2circle(_rect2pts(rect),circle)

def _rect2pts(rect):
    '''returns the corners of a rectangle
    >>> _rect2pts((0,1,4,5))
    ((0, 1), (0, 6), (4, 6), (4, 1))
    '''
    (x,y,w,h) = rect
    return (x,y),(x,y+h),(x+w,y+h),(x+w,y)

def poly2line(pts,(p1,p2)):
    '''collide a polygon with a line
    *this is tested by other methods*'''
    for i,pt1 in enumerate(pts):
        pt2 = pts[i-1]
        if line2line((pt1,pt2),(p1,p2)):
            return True
    return False

def poly2circle(pts, circle):
    '''collide a polygon with a circle
    *this is tested by other methods*'''
    for i,pt1 in enumerate(pts):
        if circle2line(circle,(pt1,pts[i-1])):
            return True
    return False

def poly2poly(pts1,pts2):
    '''collide a polygon with a polygon
    *this is tested by other methods*'''
    for i,pt1 in enumerate(pts1):
        pt2 = pts1[i-1]
        if poly2line(pts2,pt1,pt2):
            return True
    return False

def dist(point1, point2):
    '''returns the pythagorean distance between two points
    >>> dist((0,0), (4,3))
    5.0
    '''
    code = """
    //double x1,x2,y1,y2;
    return_val = sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1));
    """
    (x1,y1) = point1
    (x2,y2) = point2
    #return weave.inline(code,['x1','x2','y1','y2'],type_converters=converters.blitz)
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

ditance = dist

def dist_to_line(point, line):
    '''get the distance from a point to a line
    @returns: (distance, closest_point_on_line)
    >>> import math
    >>> dist_to_line((0,0),((2,0),(0,2)))[0] == math.sqrt(2)
    True
    >>> dist_to_line((0,1),((2,0),(2,2)))
    (2, (2, 1))
    '''
    (a,b) = point
    ((x1,y1),(x2,y2)) = line
    if x2==x1:
        return abs(x1-a),(x1,b)
    elif y2==y1:
        return abs(y1-b),(a,y1)
    m1 = (y2-y1)/float(x2-x1)
    m2 = -1/m1
    x = (m1*x1-m2*a+b-y1)/(m1-m2)
    y = m1*(x-x1)+y1
    return dist((a,b),(x,y)),(x,y)

if __name__=='__main__':
    import doctest
    doctest.testmod()
