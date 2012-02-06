#
# furl: URL manipulation made simple.
#
# Arthur Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: Build Amazing Things (Unlicense)

import re
import abc
import urllib
import urlparse
import warnings

from omdict1D import omdict1D

_absent = object()

#
# TODO(grun): Subclass Path, PathCompositionInterface, Query, and
# QueryCompositionInterface into two subclasses each - one for the URL and one
# for the Fragment.
#
# Subclasses here will clean up the code because the valid encodings are
# different between a URL Path and a Fragment Path and a URL Query and a
# Fragment Query.
#
# For example, '?' and '#' don't need to be encoded in Fragment Path segments
# but they must be encoded in URL Path segments.
#
# Similarly, '#' doesn't need to be encoded in Fragment Query keys and values,
# but must be encoded in URL Query keys and values.
#
# Also, force_absolute_if_not_empty is True in URL Paths but False in Fragment
# Paths. This is already handled, but its implementation can change once the new
# classes are implemented.
#

class Path(object):
  """
  Represents a URL path comprised of zero or more path segments.

    http://tools.ietf.org/html/rfc3986#section-3.3

  Path parameters are currently not supported.

  Attributes:
    _absolute_if_not_empty: Boolean whether or not isabsolute should be forced
      to True if the path is non-empty. If true, isabsolute is read
      only. _absolute_if_not_empty is True for URL paths, False for Fragment
      paths. URL paths are always absolute (isabsolute is True) if they are not
      empty, and thus the user shouldn't be able to set isabsolute, only read
      it. Fragment paths can be optionally absolute, and thus it makes sense to
      allow the user to set isabsolute to True or False.
    segments: List of zero or more path segments comprising this path. If the
      path string has a trailing '/', the last segment will be '' and self.isdir
      will be True and self.isfile will be False. An empty segment list
      represents an empty path, not '/' (though they have the same meaning).
    isabsolute: Boolean whether or not this is an absolute path or not. An
      absolute path starts with a '/'. self.isabsolute is False if the path is
      empty (self.segments == [] and str(path) == '').
    strict: Boolean whether or not UserWarnings should be raised if improperly
      encoded path strings are provided to methods that take such strings, like
      load(), add(), set(), remove(), etc.
  """
  SAFE_SEGMENT_CHARS = ":@-._~!$&'()*+,;="
  
  def __init__(self, path='', absolute_if_not_empty=False, strict=False):
    self.segments = []

    self.strict = strict
    self._isabsolute = False
    self._absolute_if_not_empty = absolute_if_not_empty

    self.load(path)

  def load(self, path):
    """
    Load <path>, replacing any existing path. <path> can either be a list of
    segments or a path string to adopt.

    Returns: <self>.
    """    
    if not path:
      segments = []
    elif hasattr(path, 'split') and callable(path.split): # String interface.
      segments = self._segments_from_path(path)
    else: # List interface.
      segments = path

    if self._absolute_if_not_empty:
      self._isabsolute = True if segments else False
    else:
      self._isabsolute = (segments and segments[0] == '')

    if self.isabsolute and len(segments) > 1 and segments[0] == '':
      segments.pop(0)
    self.segments = [urllib.unquote(segment) for segment in segments]

    return self

  def add(self, path):
    """
    Add <path> to the existing path. <path> can either be a list of segments or
    a path string to append to the existing path.

    Returns: <self>.
    """
    newsegments = path # List interface.
    if hasattr(path, 'split') and callable(path.split): # String interface.
      newsegments = self._segments_from_path(path)

    # Preserve the opening '/' if one exists already (self.segments == ['']).
    if self.segments == [''] and newsegments and newsegments[0] != '':
      newsegments.insert(0, '')

    self.load(join_path_segments(self.segments, newsegments))
    return self

  def set(self, path):
    self.load(path)
    return self

  def remove(self, path):
    if path is True:
      self.load('')
    else:
      segments = path # List interface.
      if isinstance(path, basestring): # String interface.
        segments = self._segments_from_path(path)
      base = ([''] if self.isabsolute else []) + self.segments
      self.load(remove_path_segments(base, segments))
    return self

  @property
  def isabsolute(self):
    if self._absolute_if_not_empty and self.segments:
      return True
    return self._isabsolute

  @isabsolute.setter
  def isabsolute(self, isabsolute):
    """
    Raises: AttributeError if _absolute_if_not_empty is True.
    """
    if self._absolute_if_not_empty:
      errstr = ('Path.isabsolute is read only for URL paths.'
                'URL paths are always absolute if not empty.')
      raise AttributeError(errstr)
    self._isabsolute = isabsolute

  @property
  def isdir(self):
    """
    Returns: True if the path ends on a directory, False otherwise. If True, the
    last segment is '', representing the trailing '/' of the path.
    """
    return self.segments == [] or (self.segments and self.segments[-1] == '')

  @property
  def isfile(self):
    """
    Returns: True if the path ends on a file, False otherwise. If True, the last
    segment is not '', representing some file as the last segment of the path.
    """
    return not self.isdir

  def __nonzero__(self):
    return len(self.segments) > 0

  def __str__(self):
    segments = list(self.segments)
    if self.isabsolute and self.segments:
      segments.insert(0, '')
    return self._path_from_segments(segments, quoted=True)
    
  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))

  def _segments_from_path(self, path):
    """
    Returns: The list of path segments from the path string <path>.

    Raises: UserWarning if <path> is an improperly encoded path string and self.strict
    is True.
    """
    # Raise a warning if self.strict is True and the user provided an improperly
    # encoded path string.
    segments = path.split('/')
    if self.strict:
      for segment in segments:
        if not is_valid_encoded_path_segment(segment):
          warnstr = (("Improperly encoded path string received: '%s'. "
                      "Proceeding, but did you mean '%s'?") %
                     (path, self._path_from_segments(segments, quoted=True)))
          warnings.warn(warnstr, UserWarning)
          break
    return map(urllib.unquote, segments)

  def _path_from_segments(self, segments, quoted=True):
    """
    Combine the provided path segments <segments> into a path string. If
    <quoted> is True, each path segment will be quoted. If <quoted> is False,
    each path segment will be unquoted.

    Returns: A path string, with either quoted or unquoted path segments.
    """
    segments_str = ''.join(segments)
    if quoted and '%' not in segments_str:
      segments = map(lambda s: urllib.quote(s, self.SAFE_SEGMENT_CHARS),
                     segments)
    elif not quoted and '%' in segments_str:
      segments = map(urllib.unquote, segments)
    return '/'.join(segments)


class PathCompositionInterface(object):
  """
  Abstract class interface for a parent class that contains a Path.
  """
  __metaclass__ = abc.ABCMeta
  def __init__(self, absolute_if_not_empty=False, strict=False):
    """
    Params:
      absolute_if_not_empty: See Path._absolute_if_not_empty.
    """
    self._path = Path(absolute_if_not_empty=absolute_if_not_empty,
                      strict=strict)

  @property
  def path(self):
    return self._path
  
  @property
  def pathstr(self):
    return str(self._path)

  def __setattr__(self, attr, value):
    """
    Returns: True if this attribute is handled and set here, False otherwise.
    """
    if attr == 'path':
      self._path.load(value)
      return True
    return False


class Query(object):
  """
  Represents a URL query comprised of zero or more unique parameters and their
  respective values.

    http://tools.ietf.org/html/rfc3986#section-3.4


  All interaction with Query.params is done with unquoted strings. So

    f.query.params['a'] = 'a%5E'

  means the intended value for 'a' is 'a%5E', not 'a^'.
  

  Query.params is implemented as an omdict1D object - a one dimensional ordered
  multivalue dictionary. This provides support for repeated URL parameters, like
  'a=1&a=2'. omdict1D is a subclass of omdict, an ordered multivalue
  dictionary. Documentation for omdict can be found here

    https://github.com/gruns/orderedmultidict

  The one dimensional aspect of omdict1D means that a list of values is
  interpreted as multiple values, not a single value which is itself a list of
  values. This is a reasonable distinction to make because URL query parameters
  are one dimensional - query parameter values cannot themselves be composed of
  sub-values.

  So what does this mean? This means we can safely interpret

    f = furl('http://www.google.com')
    f.query.params['arg'] = ['one', 'two', 'three']

  as three different values for 'arg': 'one', 'two', and 'three', instead of a
  single value which is itself some serialization of the python list ['one',
  'two', 'three']. Thus, the result of the above will be

    f.query.allitems() == [('arg','one'), ('arg','two'), ('arg','three')]

  and not

    f.query.allitems() == [('arg', ['one', 'two', 'three'])]

  The latter doesn't make sense because query parameter values cannot be
  composed of sub-values. So finally

    str(f.query) == 'arg=one&arg=two&arg=three'

  Attributes:
    params: Ordered multivalue dictionary of query parameter key:value
      pairs. Parameters in self.params are maintained URL decoded - 'a b' not
      'a+b'.
    strict: Boolean whether or not UserWarnings should be raised if improperly
      encoded query strings are provided to methods that take such strings, like
      load(), add(), set(), remove(), etc.
  """
  SAFE_KEY_CHARS   = "/?:@-._~!$'()*+,"
  SAFE_VALUE_CHARS = "/?:@-._~!$'()*+,="
  
  def __init__(self, query='', strict=False):
    self.strict = strict

    self._params = omdict1D()

    self.load(query)

  def load(self, query):
    self.params.load(self._items(query))
    return self

  def add(self, args):
    for param, value in self._items(args):
      self.params.add(param, value)
    return self

  def set(self, mapping):
    """
    Adopt all mappings in <mapping>, replacing any existing mappings with the same
    key. If a key has multiple values in <mapping>, they are all adopted.

    Examples:
      Query({1:1}).set([(1,None),(2,2)]).params.allitems() == [(1,None),(2,2)]
      Query({1:None,2:None}).set([(1,1),(2,2),(1,11)]).params.allitems()
        == [(1,1),(2,2),(1,11)]
      Query({1:None}).set([(1,[1,11,111])]).params.allitems()
        == [(1,1),(1,11),(1,111)]

    Returns: <self>.
    """
    self.params.updateall(mapping)
    return self

  def remove(self, query):
    if query is True:
      self.load('')
    else:
      keys = [query]
      if hasattr(query, '__iter__') and callable(query.__iter__):
        keys = query
      for key in keys:
        self.params.pop(key, None)
    return self

  @property
  def params(self):
    return self._params

  @params.setter
  def params(self, params):
    items = self._items(params)

    self._params.clear()
    for key, value in items:
      self._params.add(key, value)

  def encode(self, delimeter='&'):
    """
    Examples:
      Query('a=a&b=#').encode() == 'a=a&b=%23'
      Query('a=a&b=#').encode(';') == 'a=a;b=%23'
    
    Returns: A URL encoded query string using <delimeter> as the delimeter
    separating key:value pairs. The most common and default delimeter is '&',
    but ';' can also be specified. ';' is W3C recommended.
    """
    pairs = []
    for key, value in self.params.iterallitems():
      pair = '='.join((urllib.quote_plus(str(key), self.SAFE_KEY_CHARS),
                       urllib.quote_plus(str(value), self.SAFE_VALUE_CHARS)))
      pairs.append(pair)
    return delimeter.join(pairs)

  def __nonzero__(self):
    return len(self.params) > 0

  def __str__(self):
    return self.encode()

  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))

  def _items(self, items):
    """
    Extract and return the key:value items from various containers. Some
    containers that could hold key:value items are

      - List of (key,value) tuples.
      - Dictionaries of key:value items.
      - Multivalue dictionary of key:value items, with potentially repeated
        keys.
      - Query string with encoded params and values.

    Keys and values are passed through unmodified unless they were passed in
    within an encoded query string, like 'a=a%20a&b=b'. Keys and values passed
    in within an encoded query string are unquoted by urlparse.parse_qsl(),
    which uses urllib.unquote_plus() internally.

    Returns: List of items as (key, value) tuples. Keys and values are passed
    through unmodified unless they were passed in as part of an encoded query
    string, in which case the final keys and values that are returned will be
    unquoted.

    Raises: UserWarning if <path> is an improperly encoded path string and self.strict
    is True.
    """
    if not items:
      items = []
    # Multivalue Dictionary-like interface. i.e. {'a':1, 'a':2, 'b':2}
    elif hasattr(items, 'allitems') and callable(items.allitems):
      items = list(items.allitems())
    elif hasattr(items, 'iterallitems') and callable(items.iterallitems):
      items = list(items.iterallitems())
    # Dictionary-like interface. i.e. {'a':1, 'b':2, 'c':3}
    elif hasattr(items, 'iteritems') and callable(items.iteritems):
      items = list(items.iteritems())
    elif hasattr(items, 'items') and callable(items.items):
      items = list(items.items())
    # Encoded query string. i.e. 'a=1&b=2&c=3'
    elif isinstance(items, basestring):
      # Raise a warning if self.strict is True and the user provided an
      # improperly encoded query string.
      if self.strict:
        pairstrs = [s2 for s1 in items.split('&') for s2 in s1.split(';')]
        pairs = map(lambda item: item.split('=', 1), pairstrs)
        pairs = map(lambda p: (p[0],'') if len(p)==1 else (p[0],p[1]), pairs)
        for key, value in pairs:
          if (not is_valid_encoded_query_key(key) or
              not is_valid_encoded_query_value(value)):
            warnstr = (("Improperly encoded query string received: '%s'. "
                        "Proceeding, but did you mean '%s'?") %
                       (items, urllib.urlencode(pairs)))
            warnings.warn(warnstr, UserWarning)
            break

      # Keys and values will be unquoted from the query string.
      items = urlparse.parse_qsl(items, keep_blank_values=True)
    # Default to list of key:value items interface. i.e. [('a','1'), ('b','2')]
    else:
      item = list(items)

    return items

  
class QueryCompositionInterface(object):
  """
  Abstract class interface for a parent class that contains a Query.
  """
  __metaclass__ = abc.ABCMeta
  def __init__(self, strict=False):
    self._query = Query(strict=strict)

  @property
  def query(self):
    return self._query

  @property
  def querystr(self):
    return str(self._query)

  @property
  def args(self):
    """
    Shortcut method to access the query parameters, self._query.params.
    """
    return self._query.params

  def __setattr__(self, attr, value):
    """
    Returns: True if this attribute is handled and set here, False otherwise.
    """
    if attr == 'args' or attr == 'query':
      self._query.load(value)
      return True
    return False


class Fragment(PathCompositionInterface, QueryCompositionInterface):
  """
  Represents a URL fragment, comprised internally of a Path and Query optionally
  separated by a '?' character.

    http://tools.ietf.org/html/rfc3986#section-3.5

  Attributes:
    path: Path object representing the path portion of this fragment.
    query: Query object representing the query portion of this fragment.
    separator: Boolean whether or not a '?' separator should be included in the
      string representation of this fragment. When False, a '?' character will
      not separate the fragment path from the fragment query in the fragment
      string. This is useful to build fragments like '#!arg1=val1&arg2=val2',
      where no separating '?' is desired.
  """
  def __init__(self, fragment='', strict=False):
    PathCompositionInterface.__init__(self, absolute_if_not_empty=False,
                                      strict=strict)
    QueryCompositionInterface.__init__(self, strict=strict)
    self.strict = strict
    self.separator = True

    self.load(fragment)

  def load(self, fragment):
    self.path.load('')
    self.query.load('')
    
    toks = fragment.split('?', 1)
    if len(toks) == 0:
      self._path.load('')
      self._query.load('')
    elif len(toks) == 1:
      # Does this fragment look like a path or a query? Default to path.
      if '=' in fragment: # Query example: '#woofs=dogs'.
        self._query.load(fragment)
      else: # Path example: '#supinthisthread'.
        self._path.load(fragment)
    else:
      # Does toks[1] actually look like a query? Like 'a=a' or 'a=' or '=a'?
      if '=' in toks[1]:
        self._path.load(toks[0])
        self._query.load(toks[1])
      # If toks[1] doesn't look like a query, the user probably provided a
      # fragment string like 'a?b?' that was intended to be adopted as-is, not a
      # two part fragment with path 'a' and query 'b?'.
      else:
        self._path.load(fragment)

  def add(self, path=_absent, args=_absent):
    if path is not _absent:
      self.path.add(path)
    if args is not _absent:
      self.query.add(args)
    return self

  def set(self, path=_absent, args=_absent, separator=_absent):
    if path is not _absent:
      self.path.load(path)
    if args is not _absent:
      self.query.load(args)
    if separator is True or separator is False:
      self.separator = separator
    return self

  def remove(self, fragment=_absent, path=_absent, args=_absent):
    if fragment is True:
      self.load('')
    if path is not _absent:
      self.path.remove(path)
    if args is not _absent:
      self.query.remove(args)
    return self

  def __setattr__(self, attr, value):
    if (not PathCompositionInterface.__setattr__(self, attr, value) and
        not QueryCompositionInterface.__setattr__(self, attr, value)):
      object.__setattr__(self, attr, value)

  def __nonzero__(self):
    return bool(self.path) or bool(self.query)

  def __str__(self):
    path, query = str(self._path), str(self._query)

    # If there is no query or self.separator is False, decode all '?' characters
    # in the path from their percent encoded form '%3F' to '?'. This allows for
    # fragment strings containg '?'s, like '#dog?machine?yes'.
    if path and (not query or not self.separator):
      path = path.replace('%3F','?')

    if query and path:
      return path + ('?' if self.separator else '') + query
    return path + query

  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))


class FragmentCompositionInterface(object):
  """
  Abstract class interface for a parent class that contains a Fragment.
  """
  __metaclass__ = abc.ABCMeta
  def __init__(self, strict=False):
    self._fragment = Fragment(strict=strict)

  @property
  def fragment(self):
    return self._fragment

  @property
  def fragmentstr(self):
    return str(self._fragment)
  
  def __setattr__(self, attr, value):
    """
    Returns: True if this attribute is handled and set here, False otherwise.
    """
    if attr == 'fragment':
      self.fragment.load(value)
      return True
    return False


class furl(PathCompositionInterface, QueryCompositionInterface,
           FragmentCompositionInterface):
  """
  Object for simple parsing and manipulation of a URL and its components.

    scheme://username:password@host:port/path?query#fragment

  Attributes:
    DEFAULT_PORTS: Map of various URL schemes to their default ports. Scheme
      strings are lowercase.
    strict: Boolean whether or not UserWarnings should be raised if improperly
      encoded path, query, or fragment strings are provided to methods that take
      such strings, like load(), add(), set(), remove(), etc.
    username: Username string for authentication.
    password: Password string for authentication with <username>.
    scheme: URL scheme ('http', 'https', etc). All lowercase.
    host: URL host (domain, IPv4 address, or IPv6 address), not including
      port. All lowercase.
    port: Port. Valid port values are 1-65535, or None meaning no port
      specified.
    netloc: Network location. Combined host and port string.
    path: Path object from PathCompositionInterface.
    query: Query object from QueryCompositionInterface.
    fragment: Fragment object from FragmentCompositionInterface.
  """
  DEFAULT_PORTS = {
    'ftp'   : 21,
    'ssh'   : 22,
    'http'  : 80,
    'https' : 443,
    }
  
  def __init__(self, url='', strict=False):
    """
    Raises: ValueError on invalid url.
    """
    PathCompositionInterface.__init__(self, absolute_if_not_empty=True,
                                      strict=strict)
    QueryCompositionInterface.__init__(self, strict=strict)
    FragmentCompositionInterface.__init__(self, strict=strict)
    self.strict = strict

    self.username = ''
    self.password = ''
    self.scheme = ''
    self._host = ''
    self._port = None

    self.load(url) # Raises ValueError on invalid url.

  def load(self, url):
    """
    Parse and load a URL.

    Raises: ValueError on invalid URL (for example malformed IPv6 address or
    invalid port).
    """
    tokens = urlsplit(url) # Raises ValueError on malformed IPv6 address.

    self.netloc = tokens.netloc # Raises ValueError.
    self.scheme = tokens.scheme.lower()
    if not self.port:
      self._port = self.DEFAULT_PORTS.get(self.scheme)
    self.path.load(tokens.path)
    self.query.load(tokens.query)
    self.fragment.load(tokens.fragment)
    return self

  @property
  def host(self):
    return self._host

  @host.setter
  def host(self, host):
    """
    Raises: ValueError on malformed IPv6 address.
    """
    urlparse.urlsplit('http://%s/' % host) # Raises ValueError.
    self._host = host

  @property
  def port(self):
    return self._port

  @port.setter
  def port(self, port):
    """
    A port value can 1-65535 or None meaning no port specified. If <port> is
    None and self.scheme is a known scheme in self.DEFAULT_PORTS, the default
    port value from self.DEFAULT_PORTS will be used.
    
    Raises: ValueError on invalid port.
    """
    if port is None:
      self._port = self.DEFAULT_PORTS.get(self.scheme)
    elif is_valid_port(port):
      self._port = int(str(port))
    else:
      raise ValueError("Invalid port: '%s'" % port)

  @property
  def netloc(self):
    userpass = self.username
    if self.password:
      userpass += ':' + self.password
    if userpass:
      userpass += '@'

    netloc = self.host
    if self.port and self.port != self.DEFAULT_PORTS.get(self.scheme):
      netloc += ':' + str(self.port)

    return userpass + netloc

  @netloc.setter
  def netloc(self, netloc):
    """
    Params:
      netloc: Network location string, like 'google.com' or 'google.com:99'.
    Raises: ValueError on invalid port or malformed IPv6 address.
    """
    # Raises ValueError on malformed IPv6 addresses.
    urlparse.urlsplit('http://%s/' % netloc)
    
    username = password = host = ''
    port = None

    if '@' in netloc:
      userpass, netloc = netloc.split('@', 1)
      if ':' in userpass:
        username, password = userpass.split(':', 1)
      else:
        username = userpass

    if ':' in netloc:
      # IPv6 address literal.
      if ']' in netloc:
        colonpos, bracketpos = netloc.rfind(':'), netloc.rfind(']')
        if colonpos > bracketpos and colonpos != bracketpos + 1:
          raise ValueError("Invalid netloc: '%s'" % netloc)
        elif colonpos > bracketpos and colonpos == bracketpos + 1:
          host, port = netloc.rsplit(':', 1)
        else:
          host = netloc.lower()
      else:
        host, port = netloc.rsplit(':', 1)
        host = host.lower()
    else:
      host = netloc.lower()

    # Avoid side effects by assigning self.port before self.host so that if an
    # exception is raised when assigning self.port self.host isn't updated.
    self.port = port # Raises ValueError on invalid port.
    self.host = host
    self.username = username
    self.password = password

  @property
  def url(self):
    return str(self)

  @url.setter
  def url(self, url):
    return self._parse(url)

  def add(self, args=_absent, path=_absent, fragment_path=_absent,
          fragment_args=_absent, query_params=_absent):
    """
    Add components to a URL and return this furl instance, <self>.

    If both <args> and <query_params> are provided, a UserWarning is raised
    because <args> is provided as a shortcut for <query_params>, not to be used
    simultaneously with <query_params>. Nonetheless, providing both <args> and
    <query_params> behaves as expected, with query keys and values from both
    <args> and <query_params> added to the query - <args> first, then
    <query_params>.

    Parameters:
      args: Shortcut for <query_params>.
      path: A list of path segments to add to the existing path segments, or a
        path string to join with the existing path string.
      query_params: A dictionary of query keys and values or list of key:value
        items to add to the query.
      fragment_path: A list of path segments to add to the existing fragment
        path segments, or a path string to join with the existing fragment path
        string.
      fragment_args: A dictionary of query keys and values or list of key:value
        items to add to the fragment's query.
    Returns: <self>.
    """
    if args is not _absent and query_params is not _absent:
      warnstr = ('Both <args> and <query_params> provided to furl.add(). <args>'
                 ' is a shortcut for <query_params>, not to be used with '
                 '<query_params>. See furl.add() documentation for more '
                 'details.')
      warnings.warn(warnstr, UserWarning)

    if path is not _absent:
      self.path.add(path)
    if args is not _absent:
      self.query.add(args)
    if query_params is not _absent:
      self.query.add(query_params)
    if fragment_path is not _absent or fragment_args is not _absent:
      self.fragment.add(path=fragment_path, args=fragment_args)
    return self

  def set(self, args=_absent, path=_absent, fragment=_absent, scheme=_absent,
          netloc=_absent, fragment_path=_absent, fragment_args=_absent,
          fragment_separator=_absent, host=_absent, port=_absent, query=_absent,
          query_params=_absent, username=_absent, password=_absent):
    """
    Set components of a url and return this furl instance, <self>.

    If any overlapping, and hence possibly conflicting, parameters are provided,
    appropriate UserWarning's will be raised. The groups of parameters that
    could potentially overlap are

      <netloc> and (<host> or <port>)
      <fragment> and (<fragment_path> and/or <fragment_args>)
      any two or all of <query>, <args>, and/or <query_params>

    In all of the above groups, the latter parameter(s) take precedence over the
    earlier parameter(s). So, for example

      furl('http://google.com/').set(netloc='yahoo.com:99', host='bing.com',
                                     port=40)

    will result in a UserWarning being raised and the url becoming

      'http://bing.com:40/'

    not

      'http://yahoo.com:99/

    Parameters:
      args: Shortcut for <query_params>.
      path: A list of path segments or a path string to adopt.
      fragment: Fragment string to adopt.
      scheme: Scheme string to adopt.
      netloc: Network location string to adopt.
      query: Query string to adopt.
      query_params: A dictionary of query keys and values or list of key:value
        items to adopt.
      fragment_path: A list of path segments to adopt for the fragment's path or
        a path string to adopt as the fragment's path.
      fragment_args: A dictionary of query keys and values or list of key:value
        items for the fragment's query to adopt.
      fragment_separator: Boolean whether or not there should be a '?' separator
        between the fragment path and fragment query.
      host: Host string to adopt.
      port: Port number to adopt.
      username: Username string to adopt.
      password: Password string to adopt.
    Raises:
      ValueError on invalid port.
      UserWarning if <netloc> and (<host> and/or <port>) are provided.
      UserWarning if <query>, <args>, and/or <query_params> are provided.
      UserWarning if <fragment> and (<fragment_path>, <fragment_args>, and/or
        <fragment_separator>) are provided.
    Returns: <self>.
    """
    if netloc is not _absent and (host is not _absent or port is not _absent):
      warnstr = ('Possible parameter overlap: <netloc> and <host> and/or '
                 '<port> provided. See furl.set() documentation for more '
                 'details.')
      warnings.warn(warnstr, UserWarning)
    if ((args is not _absent and query is not _absent) or
        (query is not _absent and query_params is not _absent) or
        (args is not _absent and query_params is not _absent)):
      warnstr = ('Possible parameter overlap: <query>, <args>, and/or'
                 '<query_params> provided. See furl.set() documentation for more'
                 'details.')
      warnings.warn(warnstr, UserWarning)
    if (fragment is not _absent and
        (fragment_path is not _absent or fragment_args is not _absent or
         (fragment_separator is not _absent))):
      warnstr = ('Possible parameter overlap: <fragment> and (<fragment_path>'
                 'and/or <fragment_args>) or <fragment> and '
                 '<fragment_separator> provided. See furl.set() documentation'
                 'for more details.')
      warnings.warn(warnstr, UserWarning)
   
    # Avoid side effects if exceptions are raised.
    oldnetloc, oldport = self.netloc, self.port
    try:
      if netloc is not _absent:
        self.netloc = netloc # Raises ValueError on invalid port or malformed IP.
      if port is not _absent:
        self.port = port # Raises ValueError on invalid port.
    except ValueError:
      self.netloc, self.port = oldnetloc, oldport
      raise

    if username is not _absent:
      self.username = username
    if password is not _absent:
      self.password = password
    if scheme is not _absent:
      self.scheme = scheme
    if host is not _absent:
      self.host = host

    if path is not _absent:
      self.path.load(path)
    if query is not _absent:
      self.query.load(query)
    if args is not _absent:
      self.query.load(args)
    if query_params is not _absent:
      self.query.load(query_params)
    if fragment is not _absent:
      self.fragment.load(fragment)
    if fragment_path is not _absent:
      self.fragment.path.load(fragment_path)
    if fragment_args is not _absent:
      self.fragment.query.load(fragment_args)
    if fragment_separator is not _absent:
      self.fragment.separator = fragment_separator
    return self

  def remove(self, args=_absent, path=_absent, fragment=_absent, query=_absent,
             query_params=_absent, port=_absent, fragment_path=_absent,
             fragment_args=_absent, username=_absent, password=_absent):
    """
    Remove components of url and return this furl instance, <self>.

    Parameters:
      args: Shortcut for query_params.
      path: A list of path segments to remove from the end of the existing path
        segments list, or a path string to remove from the end of the existing
        path string, or True to remove the path entirely.
      query: If True, remove the query portion of the URL entirely.
      query_params: A list of query keys to remove from the query, if they
        exist.
      port: If True, remove the port from the network location string, if it
        exists.
      fragment: If True, remove the fragment portion of the URL entirely.
      fragment_path: A list of path segments to remove from the end of the
        fragment's path segments or a path string to remove from the end of the
        fragment's path string.
      fragment_args: A list of query keys to remove from the fragment's query,
        if they exist.
      username: If True, remove the username, if it exists.
      password: If True, remove the password, if it exists.
    Returns: <self>.
    """
    if username:
      self.username = ''
    if password:
      self.password = ''
    if port:
      self.port = None

    if path is not _absent:
      self.path.remove(path)
    if args is not _absent:
      self.query.remove(args)
    if query is not _absent:
      self.query.remove(query)
    if fragment is not _absent:
      self.fragment.remove(fragment)
    if query_params is not _absent:
      self.query.remove(query_params)
    if fragment_path is not _absent:
      self.fragment.path.remove(fragment_path)
    if fragment_args is not _absent:
      self.fragment.query.remove(fragment_args)
    return self

  def __setattr__(self, attr, value):
    if (not PathCompositionInterface.__setattr__(self, attr, value) and
        not QueryCompositionInterface.__setattr__(self, attr, value) and
        not FragmentCompositionInterface.__setattr__(self, attr, value)):
      object.__setattr__(self, attr, value)

  def __str__(self):
    tokens = (self.scheme, self.netloc, self.pathstr, self.querystr,
              self.fragmentstr)
    return urlparse.urlunsplit(tokens)

  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))


def urlsplit(url):
  """
  urlparse.urlsplit() doesn't separate the query string from the path for
  schemes not in the list urlparse.uses_query, but furl should support proper
  parsing of query strings and paths for any scheme users decide to use (custom
  schemes, internal schemes, etc).

  So as a workaround, use 'http', a scheme in urlparse.uses_query, for the
  purposes of urlparse.urlsplit(), but then revert back to the original scheme
  provided.

  Parameters:
    url: URL string to split.

  Returns: urlparse.SplitResult tuple subclass, just like urlparse.urlsplit()
  returns, with fields (scheme, netloc, path, query, fragment, username,
  password, hostname, port). See the url below for more details on urlsplit().

    http://docs.python.org/library/urlparse.html#urlparse.urlsplit
  """
  def _change_urltoks_scheme(tup, scheme):
    l = list(tup)
    l[0] = scheme
    return tuple(l)
    
  toks = urlparse.urlsplit(url)
  if not toks.scheme or toks.scheme in urlparse.uses_query:
    return toks

  original_scheme = toks.scheme
  httpurl = _change_urltoks_scheme(toks, 'http')
  toks = urlparse.urlsplit(urlparse.urlunsplit(httpurl))
  return urlparse.SplitResult(*_change_urltoks_scheme(toks, original_scheme))

def join_path_segments(*args):
  """
  Join multiple lists of path segments together, intelligently handling path
  segments borders to preserve intended slashes of the final constructed path.

  This function is not encoding aware - it does not test for or change the
  encoding of path segments it is passed.

  Examples:
    join_path_segments(['a'], ['b']) == ['a','b']
    join_path_segments(['a',''], ['b']) == ['a','b']
    join_path_segments(['a'], ['','b']) == ['a','b']
    join_path_segments(['a',''], ['','b']) == ['a','','b']
    join_path_segments(['a','b'], ['c','d']) == ['a','b','c','d']

  Returns: A list containing the joined path segments.
  """
  finals = []
  for segments in args:
    if not segments or segments == ['']:
      continue
    elif not finals:
      finals.extend(segments)
    else:
      # Example #1: ['a',''] + ['b'] == ['a','b']
      # Example #2: ['a',''] + ['','b'] == ['a','','b']
      if finals[-1] == '' and (segments[0] != '' or len(segments) > 1):
        finals.pop(-1)
      # Example: ['a'] + ['','b'] == ['a','b']
      elif finals[-1] != '' and segments[0] == '' and len(segments) > 1:
        segments = segments[1:]
      finals.extend(segments)
  return finals

def remove_path_segments(segments, remove):
  """
  Removes the path segments of <remove> from the end of the path segments
  <segments>.

  Examples:
    # '/a/b/c' - 'b/c' == '/a/'
    remove_path_segments(['','a','b','c'], ['b','c']) == ['','a','']
    # '/a/b/c' - '/b/c' == '/a'
    remove_path_segments(['','a','b','c'], ['','b','c']) == ['','a']

  Returns: The list of all remaining path segments after the segments in
  <remove> have been removed from the end of <segments>. If no segments from
  <remove> were removed from <segments>, <segments> is returned unmodified.
  """
  # [''] means a '/', which is properly represented by ['', ''].
  if segments == ['']:
    segments.append('')
  if remove == ['']:
    remove.append('')

  ret = None
  if remove == segments:
    ret = []
  elif len(remove) > len(segments):
    ret = segments
  else:
    toremove = list(remove)

    if len(remove) > 1 and remove[0] == '':
      toremove.pop(0)

    if toremove and toremove == segments[-1 * len(toremove):]:
      ret = segments[:len(segments) - len(toremove)]
      if remove[0] != '' and ret:
        ret.append('')
    else:
      ret = segments

  return ret

def is_valid_port(port):
  port = str(port)
  if not port.isdigit() or int(port) == 0 or int(port) > 65535:
    return False
  return True

#
# TODO(grun): These functions need to be expanded to reflect the fact that the
# valid encoding for a URL Path segment is different from a Fragment Path
# segment, and valid URL Query key and value encoding is different than valid
# Fragment Query key and value encoding.
#
# For example, '?' and '#' don't need to be encoded in Fragment Path segments
# but they must be encoded in URL Path segments.
#
# Similarly, '#' doesn't need to be encoded in Fragment Query keys and values,
# but must be encoded in URL Query keys and values.
#
# Perhaps merge them with URLPath, FragmentPath, URLQuery, and FragmentQuery
# when those new classes are created (see the TODO currently at the top of the
# source, 02/03/2012).
#

# RFC 3986
#   unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
#
#   pct-encoded = "%" HEXDIG HEXDIG
#
#   sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
#                 / "*" / "+" / "," / ";" / "="
#
#   pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#
#   ====
#   Path
#   ====
#   segment       = *pchar
#
#   =====
#   Query
#   =====
#   query       = *( pchar / "/" / "?" )
#
VALID_ENCODED_PATH_SEGMENT_REGEX = re.compile(
  r'^([\w\-\.\~\:\@\!\$\&\'\(\)\*\+\,\;\=]|(\%[\da-fA-F][\da-fA-F]))*$')
def is_valid_encoded_path_segment(segment):
  return bool(VALID_ENCODED_PATH_SEGMENT_REGEX.match(segment))

VALID_ENCODED_QUERY_KEY_REGEX = re.compile(
  r'^([\w\-\.\~\:\@\!\$\&\'\(\)\*\+\,\;\/\?]|(\%[\da-fA-F][\da-fA-F]))*$')
def is_valid_encoded_query_key(key):
  return bool(VALID_ENCODED_QUERY_KEY_REGEX.match(key))

VALID_ENCODED_QUERY_VALUE_REGEX = re.compile(
  r'^([\w\-\.\~\:\@\!\$\&\'\(\)\*\+\,\;\/\?\=]|(\%[\da-fA-F][\da-fA-F]))*$')
def is_valid_encoded_query_value(value):
  return bool(VALID_ENCODED_QUERY_VALUE_REGEX.match(value))
