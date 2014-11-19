import sys


if list(sys.version_info[:2]) >= [2, 7]:
    import unittest
    from collections import OrderedDict
else:
    import unittest2 as unittest
    from ordereddict import OrderedDict

if sys.version_info[0] == 2:
    basestring = basestring
else:
    basestring = (str, bytes)

class UnicodeMixin(object):
    """
    Mixin class to handle defining the proper __str__/__unicode__ methods in
    Python 2 or 3.
    """
    if sys.version_info[0] >= 3: # Python 3
        def __str__(self):
            return self.__unicode__()
    else:  # Python 2
        def __str__(self):
            return self.__unicode__().encode('utf8')
