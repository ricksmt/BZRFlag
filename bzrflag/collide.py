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

def line2point(((x1,y1),(x2,y2)),(x,y)):
    if (x1==x2):
        return x==x1 and y1<=y<=y2 and (x,y)
    m = (y2-y1)/(x2-x1)
    # y - y1 = m(x-x1)
    online =  y - y1 == m*(x-x1)
    return online and rect2point((x1,y1,x2-x1,y2-y1),(x,y))

def line2line(((x1,y1),(x2,y2)),((a1,b1),(a2,b2)),log=False):
    if x2==x1:
        x=x1
        m1 = (b2-b1)/float(a2-a1)
    elif a2==a1:
        x=a1
        m1 = (y2-y1)/float(x2-x1)
    else:
        m1 = (y2-y1)/float(x2-x1)
        m2 = (b2-b1)/float(a2-a1)
        if m1==m2:
            return False
        x = round((m1*x1-m2*a1+b1-y1)/float(m1-m2),5)
    y = round(m1*(x-x1)+y1,5)
    if log:
        print [(x1,y1),(x2,y2),(a1,b1),(a2,b2)],[x,y],(rect2point((x1,y1,x2-x1,y2-y1),(x,y)),rect2point((a1,b1,a2-a1,b2-b1),(x,y)))
    #assert y == m2*(x-a1)+b1
    return (rect2point((x1,y1,x2-x1,y2-y1),(x,y)) and rect2point((a1,b1,a2-a1,b2-b1),(x,y))) and (x,y)

def circle2point((p,r),p2):
    return dist(p,p2)<=r and p2

def circle2line((c,r),(p1,p2)):
    d,pos = dist_to_line(c,(p1,p2))
    #print d,pos
    if d>r:
        return False
    x,y=p1
    a,b=p2
    if rect2point((x,y,a-x,b-y),pos):
        return pos
    return circle2point((c,r),p1) or circle2point((c,r),p2)

def circle2circle((c1,r1),(c2,r2)):
    return dist(c1,c2)<=r1+r2

def rect2point((x,y,w,h),(x1,y1)):
    if w<0:
        x+=w
        w*=-1
    if h<0:
        y+=h
        h*=-1
    return x<=x1<=x+w and y<=y1<=y+h

def rect2line(rect,(p1,p2)):
    return poly2line(_rect2pts(rect),p1,p2)

def rect2rect(rect1,rect2):
    return poly2poly(_rect2pts(rect1),_rect2pts(rect2))

def _rect2pts((x,y,w,h)):
    return (x,y),(x,y+h),(x+w,y+h),(x+w,y)

def poly2line(pts,(p1,p2)):
    for i,pt1 in enumerate(pts):
        pt2 = pts[i-1]
        if line2line(pt1,pt2,p1,p2):
            return True
    return False

def poly2circle(pts, circle):
    for i,pt1 in enumerate(pts):
        if circle2line(circle,(pt1,pts[i-1])):
            return True
    return False

def poly2poly(pts1,pts2):
    for i,pt1 in enumerate(pts1):
        pt2 = pts1[i-1]
        if poly2line(pts2,pt1,pt2):
            return True
    return False

def dist((x1,y1),(x2,y2)):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

def dist_to_line((a,b),((x1,y1),(x2,y2))):
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
    def test_dist():
        return dist((-1,-1),(2,3))==5
