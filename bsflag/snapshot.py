import types
import inspect
import re

_cache = {}

def getclassname(class_):
    source = inspect.getsource(class_)
    name = re.findall('class\s+([\w$_]+)\s*(?:\([^\)]+\))?:',source)
    if not name:
        raise Exception,'invalid class found %s'%source
    return name[0]

def snapshot(obj):
    name = getclassname(obj.__class__)
    print obj,name,inspect.getmodule(obj,obj.__class__)
    if not _cache.has_key(name):
        _cache[name] = [name]
        for k,v in obj.__dict__.items():
            print k,v,isinstance(v,types.InstanceType),hasattr(v,'__class__')
            if isinstance(v,types.InstanceType):
                _cache[name].append([k,snapshot(v)])
    return _cache[name]

class a:
    def __init__(self):
        self.x=5
        self.y=b()
        self.z=a
        self.w=c()

class b(a):
    def __init__(self):
        self.e=4
        self.d='hi'

class c:pass

print snapshot(a())
