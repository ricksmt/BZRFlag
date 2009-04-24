"""World Model

We try to follow what BZFlag does.  In the original, parsing is implemented in
src/bzfs/BZWReader.cxx, with individual object types are defined and parsed in
Custom*.cxx.  Going to the directory and running 'grep "str.*cmp" *' can be
informative.
"""

class BZObject(object):
    pass

class Box(BZObject):
    position, rotation, size
    pass

class Base(BZObject):
    pass


# vim: et sw=4 sts=4
