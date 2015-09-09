# -*- coding: utf-8 -*-

#
# furl - URL manipulation made simple.
#
# Arthur Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: Build Amazing Things (Unlicense)

import sys

if sys.version_info[0] == 2:
    basestring = basestring
else:
    basestring = (str, bytes)

if list(sys.version_info[:2]) >= [2, 7]:
    from collections import OrderedDict
else:
    from ordereddict import OrderedDict

class UnicodeMixin(object):
    """
    Mixin class to handle defining the proper __str__/__unicode__ methods in
    Python 2 or 3.
    """
    if sys.version_info[0] >= 3:  # Python 3
        def __str__(self):
            return self.__unicode__()
    else:  # Python 2
        def __str__(self):
            return self.__unicode__().encode('utf8')
