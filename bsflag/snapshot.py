import types
import inspect
import re
import yapgvb

_cache = {}
_modules = []

def init(moduleslist):
    global _modules
    _modules = moduleslist

def getclassname(class_):
    source = inspect.getsource(class_)
    name = re.findall('class\s+([\w$_]+)\s*(?:\([^\)]+\))?:',source)
    if not name:
        raise Exception,'invalid class found %s'%source
    return name[0]

def snapshot(obj):
    name = getclassname(obj.__class__)
    if not _cache.has_key(name):
        _cache[name] = []
        for k,v in obj.__dict__.items():
            if hasattr(v,'__class__') and inspect.getmodule(v.__class__) in _modules:
                snapshot(v)
                _cache[name].append([k,getclassname(v.__class__),v.__class__.__module__])
            elif type(v) in (list,tuple):
                lobjs = []
                lclasses = set()
                for sub in v:
                    if hasattr(sub,'__class__') and inspect.getmodule(sub.__class__) in _modules and sub.__class__ not in lclasses:
                        lobjs.append(sub)
                        lclasses.add(sub.__class__)
                for sub in lobjs:
                    snapshot(sub)
                    _cache[name].append([k+'[]',getclassname(sub.__class__),sub.__class__.__module__])
            else:
                _cache[name].append([k,False,''])

def _render(classname,mod,graph,rendered={}):
    if not _cache.has_key(classname):
        raise Exception,'not snapshotted'
    if rendered.has_key(classname):
        return rendered[classname]
    node = graph.add_node(classname,label=mod+'.'+classname)
    rendered[classname] = node
    for k,name,mod in _cache[classname]:
        subn = graph.add_node(classname+'.'+k,label=k)
        node >> subn
        if name:
            subn >> _render(name,mod,graph,rendered)
    return node

def render(obj):
    snapshot(obj)
    classname = getclassname(obj.__class__)
    graph = yapgvb.Digraph()
    node = _render(classname,'',graph,{})
    graph.layout(yapgvb.engines.dot)
    graph.render(classname + '-structure.png')

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
