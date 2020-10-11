# -*- coding: utf-8 -*-

#
# furl - URL manipulation made simple.
#
# Ansgar Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: Build Amazing Things (Unlicense)
#

from .furl import *  # noqa
from .__version__ import (  # noqa
    __title__, __version__, __license__, __author__, __contact__, __url__,
    __description__)

__all__ = ["furl"]

# Alternative
# from . import __version__ as v, furl
# __version__ = v.__version__
# __title__ = v.__title__
# etc.
