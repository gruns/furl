#
# furl: URL manipulation made simple.
#
# Arthur Grunseid
# grunseid.com
# grunseid@gmail.com
#
# Copyright: LOLOLOL
#
# License: Build Amazing Things (Unlicense)

import abc
import urllib
import urlparse
import warnings

class Path(object):
  """
  Represents a URL path comprised of zero or more path segments.

    http://tools.ietf.org/html/rfc3986#section-3.3

  Path parameters are currently not supported.

  Attributes:
    segments: List of zero or more path segments comprising this path. If the
      path string has a trailing '/', the last segment will be '' and self.isdir
      will be True and self.isfile will be False. An empty segment list
      represents an empty path, not '/' (though they have the same meaning).
    isabsolute: Boolean whether or not this is an absolute path or not. An
      absolute path starts with a '/'. self.isabsolute is False if the path is
      empty (self.segments == [] and str(path) == '').
  """
  def __init__(self, path=''):
    self.segments = []
    self.isabsolute = False

    if path:
      self.parse(path)

  def parse(self, path=''):
    self.isabsolute = (path and path[0] == '/')
    
    if isinstance(path, list):
      segments = url_path_join(*path).split('/')
    else:
      segments = path.split('/')

    if len(segments) > 1 and segments[0] == '':
      segments.pop(0)
    self.segments = [urllib.unquote(segment) for segment in segments]

  def add(self, path=None):
    """
    Add <path> to the existing path. <path> can either be a list of segments or
    a string to append to the existing path.

    Returns: <self>.
    """
    if path:
      if isinstance(path, list):
        if self.segments[-1] == '':
          self.segments.pop(-1)
        self.segments += path
      else:
        self.parse(url_path_join(str(self), path))
    return self

  def set(self, path=None):
    if path:
      self.parse(path)
    return self

  def remove(self, path=None):
    if path:
      if path == True:
        self.parse('')
      elif isinstance(path, list):
        self.parse(url_path_remove(str(self), '/'.join(path)))
      else:
        self.parse(url_path_remove(str(self), path))
    return self

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

  def __str__(self):
    if self.segments and self.isabsolute:
      return '/'.join([''] + self.segments)
    return '/'.join(self.segments)
    
  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))


class PathCompositionInterface(object):
  """
  Abstract class interface for a parent class that contains a Path.
  """
  __metaclass__ = abc.ABCMeta
  def __init__(self):
    self._path = Path()

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
      self._path.parse(value)
      return True
    return False


class Query(object):
  """
  Represents a URL query comprised of zero or more unique parameters and their
  respective values.

    http://tools.ietf.org/html/rfc3986#section-3.4

  Repeated URL parameters, like 'a=1&a=2', are deprecated to their first value,
  'a=1'. This is a tradeoff in favor of ease of use over the rarely needed
  flexibility of repeated query parameters. As a result, interacting with query
  parameters can be performed with strings instead of lists of strings.

    if furl('...').args['meat'] == 'pumps':
      ...

  instead of 

    val = furl('...').args['meat']
    if len(val) == 1 and val[0] == 'pumps':
      ...

  In the future, support for repeated URL parameters could be added, possibly
  with a a constructor argument like repeated_params=True.

  Attributes:
    params: Dictionary of query parameter key:value pairs. Parameters in
      self.params are maintained URL decoded, 'a b' not 'a+b'.
  """
  def __init__(self, query=None):
    self.params = {}
    if query:
      self.parse(query)

  def parse(self, query):
    if isinstance(query, dict):
      # py2.7+: {k:urllib.unquote_plus(v) for k, v in query.iteritems()}
      tmp = dict((k,urllib.unquote_plus(v)) for (k,v) in query.iteritems())
      self.params = tmp
    else:
      self.params = parse_qs(query)

  def add(self, args=None):
    if args:
      for param, value in args.iteritems():
        self.params[param] = value
    return self

  def set(self, query=None):
    if query:
      self.parse(query)
    return self

  def remove(self, query=None):
    if query == True:
      self.parse('')
    elif isinstance(query, list):
      for key in query:
        self.params.pop(key, None)
    return self

  def __str__(self):
    # py2.7+: {str(key):str(val) for key, val in self.params.iteritems()}
    params = dict((str(key),str(val)) for (key,val) in self.params.iteritems())
    return urllib.urlencode(params)

  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))


class QueryCompositionInterface(object):
  """
  Abstract class interface for a parent class that contains a Query.
  """
  __metaclass__ = abc.ABCMeta
  def __init__(self):
    self._query = Query()

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
      self._query.parse(value)
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
  def __init__(self, fragment=''):
    PathCompositionInterface.__init__(self)
    QueryCompositionInterface.__init__(self)
    self.separator = True

    if fragment:
      self.parse(fragment)

  def parse(self, fragment):
    self.path.parse('')
    self.query.parse('')
    self.separator = True
    
    toks = fragment.split('?', 1)
    if len(toks) == 0:
      self._path.parse('')
      self._query.parse('')
    elif len(toks) == 1:
      # Does this fragment look like a path or a query? Default to path.
      if '=' in fragment: # ex: '#variable=value'
        self._query.parse(fragment)
      else: # ex: '#supinthisthread'
        self._path.parse(fragment)
    else:
      self._path.parse(toks[0])
      self._query.parse(toks[1])

  def add(self, path=None, args=None):
    self.path.add(path)
    self.query.add(args)
    return self

  def set(self, path=None, args=None, separator=None):
    self.path.set(path)
    self.query.set(args)
    if separator == True or separator == False:
      self.separator = separator
    return self

  def remove(self, fragment=None, path=None, args=None):
    if fragment == True:
      self.parse('')
    self.path.remove(path)
    self.query.remove(args)
    return self

  def __setattr__(self, attr, value):
    if (not PathCompositionInterface.__setattr__(self, attr, value) and
        not QueryCompositionInterface.__setattr__(self, attr, value)):
      object.__setattr__(self, attr, value)

  def __str__(self):
    path, query = str(self._path), str(self._query)
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
  def __init__(self):
    self._fragment = Fragment()

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
      self.fragment.parse(value)
      return True
    return False


class furl(PathCompositionInterface, QueryCompositionInterface,
           FragmentCompositionInterface):
  """
  Represents a URL comprised of six components

    scheme://host:port/path?query#fragment

  Attributes:
    DEFAULT_PORTS: Map of various URL schemes to their default ports. Scheme
      strings are lowercase.
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
    'http'  : 80,
    'https' : 443,
    }
  
  def __init__(self, url=None):
    """
    Raises: ValueError on invalid url.
    """
    PathCompositionInterface.__init__(self)
    QueryCompositionInterface.__init__(self)
    FragmentCompositionInterface.__init__(self)

    self.scheme = ''
    self._host = ''
    self._port = None

    if url:
      self.parse(url) # Raises ValueError on invalid url.

  def parse(self, url):
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
    self.path.parse(tokens.path)
    self.query.parse(tokens.query)
    self.fragment.parse(tokens.fragment)
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
    elif isvalidport(port):
      self._port = int(str(port))
    else:
      raise ValueError("Invalid port: '%s'" % port)

  @property
  def netloc(self):
    netloc = self.host
    if self.port and self.port != self.DEFAULT_PORTS.get(self.scheme):
      netloc = '%s:%i' % (self.host, self.port)
    return netloc

  @netloc.setter
  def netloc(self, netloc):
    """
    Params:
      netloc: Network location string, like 'google.com' or 'google.com:99'.
    Raises: ValueError on invalid port or malformed IPv6 address.
    """
    # Raises ValueError on malformed IPv6 addresses.
    urlparse.urlsplit('http://%s/' % netloc)
    
    host = port = None
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

  @property
  def url(self):
    return str(self)

  @url.setter
  def url(self, url):
    return self._parse(url)

  def add(self, args=None, path=None, fragment_path=None, fragment_args=None,
          query_params=None):
    """
    Add components to a URL and return this furl instance, <self>.

    Existing URL parameters that conflict with values to be added in <args> or
    <query_params> will be overwritten with the new values in <args> or
    <query_params>. For example

      furl('http://www.google.com/?a=OLD&b=b').add(params={'a':'NEW', 'c':'c'})

    will overwrite the old value of parameter 'a' with the new value of
    parameter 'a' provided in <args>. The resulting URL would be

      'http://www.google.com/?a=NEW&b=b&c=c'

    If both <args> and <query_params> are provided, a UserWarning is raised
    because their values could overlap and thus potentially conflict. If their
    values conflict, <query_params> takes precedence over <args>.

    Parameters:
      args: Shortcut for <query_params>.
      path: A list of path segments to add to the existing path segments, or a
        path string to join with the existing path string.
      query_params: A dictionary of query keys and values to add to the query.
      fragment_path: A list of path segments to add to the existing fragment
        path segments, or a path string to join with the existing fragment path
        string.
      fragment_args: A dictionary of query keys and values to add to the
        fragment's query.
    Returns: <self>.
    """
    if args and query_params:
      warnstr = ('Possible parameter overlap: both <args> and <query_params>'
                 'provided. See furl.add() documentation for more details.')
      warnings.warn(warnstr, UserWarning)
    
    self.path.add(path)
    self.query.add(args)
    self.query.add(query_params)
    self.fragment.add(path=fragment_path, args=fragment_args)
    return self

  def set(self, args=None, path=None, fragment=None, scheme=None, netloc=None,
          fragment_path=None, fragment_args=None, fragment_separator=None,
          host=None, port=None, query=None, query_params=None):
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
      args: Shortcut for query_params.
      path: A list of path segments or a path string to adopt.
      fragment: Fragment string to adopt.
      scheme: Scheme string to adopt.
      netloc: Network location string to adopt.
      query: Query string to adopt.
      query_params: A dictionary of query keys and values to adopt.
      fragment_path: A list of path segments to adopt for the fragment's path or
        a path string to adopt as the fragment's path.
      fragment_args: A dictionary of query keys and values for the fragment's
        query to adopt.
      fragment_separator: Boolean whether or not there should be a '?' separator
        between the fragment path and fragment query.
      host: Host string to adopt.
      port: Port number to adopt.
    Raises:
      ValueError on invalid port.
      UserWarning if <netloc> and (<host> and/or <port>) are provided.
      UserWarning if <query>, <args>, and/or <query_params> are provided.
      UserWarning if <fragment> and (<fragment_path>, <fragment_args>, and/or
        <fragment_separator>) are provided.
    Returns: <self>.
    """
    if netloc and (host or port):
      warnstr = ('Possible parameter overlap: <netloc> and <host> and/or '
                 '<port> provided. See furl.set() documentation for more '
                 'details.')
      warnings.warn(warnstr, UserWarning)
    if (args and query) or (query and query_params) or (args and query_params):
      warnstr = ('Possible parameter overlap: <query>, <args>, and/or'
                 '<query_params> provided. See furl.set() documentation for more'
                 'details.')
      warnings.warn(warnstr, UserWarning)
    if (fragment and (fragment_path or fragment_args or
                      (fragment_separator is not None))):
      warnstr = ('Possible parameter overlap: <fragment> and (<fragment_path>'
                 'and/or <fragment_args>) or <fragment> and <fragment_separator>'
                 'provided. See furl.set() documentation for more details.')
      warnings.warn(warnstr, UserWarning)
   
    # Avoid side effects if exceptions are raised.
    oldnetloc, oldport = self.netloc, self.port
    try:
      if netloc:
        self.netloc = netloc # Raises ValueError on invalid port or malformed IP.
      if port:
        self.port = port # Raises ValueError on invalid port.
    except ValueError:
      self.netloc, self.port = oldnetloc, oldport
      raise

    if scheme:
      self.scheme = scheme
    if host:
      self.host = host

    self.path.set(path)
    self.query.set(query)
    self.query.set(args)
    self.query.set(query_params)
    if fragment:
      self.fragment.parse(fragment)
    self.fragment.set(path=fragment_path, args=fragment_args,
                      separator=fragment_separator)

    return self

  def remove(self, args=None, path=None, fragment=None, query=None,
             query_params=None, port=None, fragment_path=None,
             fragment_args=None):
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
    Returns: <self>.
    """
    if port:
      self.port = None
    self.path.remove(path)
    self.query.remove(args)
    self.query.remove(query)
    self.fragment.remove(fragment)
    self.query.remove(query_params)
    self.fragment.path.remove(fragment_path)
    self.fragment.query.remove(fragment_args)
    return self

  def __setattr__(self, attr, value):
    if (not PathCompositionInterface.__setattr__(self, attr, value) and
        not QueryCompositionInterface.__setattr__(self, attr, value) and
        not FragmentCompositionInterface.__setattr__(self, attr, value)):
      object.__setattr__(self, attr, value)

  def __str__(self):
    tokens = (self.scheme, self.netloc, urllib.quote(self.pathstr),
              self.querystr, self.fragmentstr)
    return urlparse.urlunsplit(tokens)

  def __repr__(self):
    return "%s('%s')" % (self.__class__.__name__, str(self))


def parse_qs(query):
  """
  Parse a query string to a dictionary of parameter key:value pairs, removing
  any duplicate url parameters. I.e. 'a=1&a=2' would become {'a':'1'}.
  """
  # py2.7+: {key:val[0] for key, val in urlparse.parse_qs(query).iteritems()}
  return dict((k,v[0]) for (k,v) in urlparse.parse_qs(query).iteritems())

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

  Returns: urlparse.SplitResult tuple subclass (just like urlparse.urlsplit()
  does) with fields (scheme, netloc, path, query, fragment, username, password,
  hostname, port). See
  http://docs.python.org/library/urlparse.html#urlparse.urlsplit for more
  details.
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

def url_path_join(*args):
  """
  Join multiple URL string paths together. Similar to os.path.join(), but for
  URL path components.

  Returns: A URL path combined from all provided paths.
  """
  tokens = []
  if args and args[0] and args[0][0] == '/':
    tokens = ['']
  for arg in args:
    tokens += filter(lambda s: s != '', arg.split('/'))
  if tokens == [''] or (args and ((arg and arg[-1] == '/') or args[-1] == '')):
    tokens.append('')
  return '/'.join(tokens)

def url_path_remove(original, toremove):
  """
  Removes the <toremove> portion from the end of the path <original>, if it
  exists.

  Returns: A URL path string with <toremove> removed from the end of
  <original>. If <toremove> cannot be removed from the end of <original>, then
  <original> is returned unmodified.
  """
  extra_slash = False
  removefrom = original
  if toremove and toremove[-1] == '/' and original and original[-1] != '/':
    removefrom = original + '/'
  elif original and original[-1] == '/' and toremove and toremove[-1] != '/':
    extra_slash = True
    removefrom = original[:-1]
  if toremove == removefrom[-1 * len(toremove):]:
    ret = removefrom[:len(removefrom) - len(toremove)]
    if extra_slash and not ret:
      ret += '/'
    return ret
  return original

def isvalidport(port):
  port = str(port)
  if not port.isdigit() or int(port) == 0 or int(port) > 65535:
    return False
  return True
