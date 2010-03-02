import plist

__all__ = ['create_array']

EMPTY_PARAM = "___EmptyParameterString___"

def create_array(*args):
    a = plist.Array()
    for arg in args:
        if isinstance(arg, basestring):
            a.append(plist.String(arg))
        elif isinstance(arg, int):
            a.append(plist.Integer(arg))
        elif arg is None:
            a.append(plist.String(EMPTY_PARAM))
    return a
