# furl API

***
### Basics

furl objects let you access and modify the six major components of a URL

    scheme://host[:port]/path?query#fragment

 * __scheme__ is the scheme string, all lowercase.
 * __host__ is the domain name, IPv4, or IPv6 address as a string. Domain names
  are all lowercase.
 * __port__ is an integer or None. A value of None means no port specified and
  the default port for the given __scheme__ should be inferred, if possible.
 * __path__ is a Path object comprised of path segments.
 * __query__ is a Query object comprised of query arguments.
 * __fragment__ is a Fragment object comprised of a Path and Query object.


***
### Scheme, Host, Port, and Network Location

__scheme__ and __host__ are strings and __port__ is an integer or None.

    ```python
    >>> f = furl('http://www.google.com:99/')
    >>> f.scheme, f.host, f.port
    ('http', 'www.google.com', 99)
    ```

furl infers the default port for common schemes, if possible

    ```python
    >>> f = furl('https://secure.google.com/')
    >>> f.port
    443

    >>> f = furl('unknown://www.google.com/')
    >>> print f.port
    None
    ```

__netloc__ is the string combination of __host__ and __port__, not including
__port__ if it is None or the default port for the provided __scheme__.

    ```python
    >>> furl('http://www.google.com/').netloc
    'www.google.com'

    >>> furl('http://www.google.com:99/').netloc
    'www.google.com:99'
    ```

***
### Path

URL paths are Path objects in furl, and are composed of zero or more path
__segments__ that can be manipulated directly. Path segments in __segments__ are
maintaned URL decoded.

    ```python
    >>> f = furl('http://www.google.com/a/larg%20ish/path')
    >>> f.path
    Path('/a/larg ish/path')
    >>> f.path.segments
    ['a', 'larg ish', 'path']
    >>> str(f.path)
    '/a/larg ish/path'
    ```

Manipulation

    ```python
    >>> f.path.segments = ['a', 'new', 'path', '']
    >>> str(f.path)
    '/a/new/path/'

    >>> f.path = 'o/hi/there/with some encoding/'
    >>> f.path.segments
    ['o', 'hi', 'there', 'with some encoding', '']
    >>> str(f.path)
    'o/hi/there/with some encoding/'

    >>> f.url
    'http://www.google.com/o/hi/there/with%20some%20encoding/'
    ```

A Path can be absolute or not, as specified by the boolean flag
__isabsolute__. While URL paths are always absolute if they aren't empty, the
__isabsolute__ boolean flag comes in handy for fragment paths, which can be
optionally absolute.

    ```python
    >>> f = furl('http://www.google.com/a/directory/#/absolute/fragment/path/')
    >>> f.path.isabsolute
    True
    >>> f.fragment.path.isabsolute
    True
    >>> f.fragment.path.isabsolute = False
    >>> f.url
    'http://www.google.com/a/directory/#absolute/fragment/path/'
    ```

A path that ends with a '/' is considered a directory, and otherwise considered
a file. The Path attribute __isdir__ returns True if the path is a directory,
False otherwise. Conversely, the attribute __isfile__ returns True if the path
is a file, False otherwise.

    ```python
    >>> f = furl('http://www.google.com/a/directory/')
    >>> f.path.isdir
    True
    >>> f.path.isfile
    False

    >>> f = furl('http://www.google.com/a/file')
    >>> f.path.isdir
    False
    >>> f.path.isfile
    True
    ```


***
### Query

URL queries are Query objects in furl, and are composed of a dictionary of query
keys and values, __params___. Query keys and values in __params__ are maintained
unquoted.

    ```python
    >>> f = furl('http://www.google.com/?one=1&two=2')
    >>> f.query
    Query('two=2&one=1')
    >>> f.query.params
    {'two': '2', 'one': '1'}
    >>> str(f.query)
    'two=2&one=1'
    ```

Manipulation

    ```python
    >>> f.query = 'three=3&four=4'
    >>> f.query.params
    {'four': '4', 'three': '3'}
    >>> f.query.params['five'] = '5'
    >>> del f.query.params['three']
    {'four': '4', 'five': '5'}
    ```

Both __furl__ and __fragment__ (covered below) objects contain a Query instance
and an __args__ attribute is provided as a shortcut to access __query.params__.

    ```python
    >>> f = furl('http://www.google.com/?one=1&two=2')
    >>> f.args
    {'two': '2', 'one': '1'}
    >>> f.query.params
    {'two': '2', 'one': '1'}
    >>> f.args == f.query.params
    True
    ```


***
### Fragment

URL fragments are Fragment objects in furl, and are composed of a __path__ and
__query__, separated by an optional '?', __separator__.

    ```python
    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> f.fragment
    Fragment('/fragment/path?with=params')
    >>> f.fragment.path
    Path('/fragment/path')
    >>> f.fragment.query
    Query('with=params')
    >>> f.fragment.separator
    True
    ```

Manipulation of Fragments is done through the Fragment's Path and Query
instances.

    ```python
    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> str(f.fragment)
    '/fragment/path?with=params'
    >>> f.fragment.path.segments.append('file.ext')
    >>> str(f.fragment)
    '/fragment/path/file.ext?with=params'

    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> str(f.fragment)
    '/fragment/path?with=params'
    >>> str(f.fragment)
    '/fragment/path?with=params'
    >>> f.fragment.args['new'] = 'yep'
    '/fragment/path/file.ext?new=yep&with=params'
    ```

Creating hash-bang fragments with furl illustrates the use of Fragment's
__separator__. When __separator__ is False, the '?' separating the Fragment's
__path__ from its __query__ isn't included.

    ```python
    >>> f = furl('http://www.google.com/')
    >>> f.fragment.path = '!'
    >>> f.fragment.args = {'a':'dic', 'of':'args'}
    >>> f.fragment.separator
    True
    >>> str(f.fragment)
    '!?a=dic&of=args'

    >>> f.fragment.separator = False
    >>> str(f.fragment)
    '!a=dic&of=args'
    >>> f.url
    'http://www.google.com/#!a=dic&of=args'
    ```


***
### Inline modification

For quick, single-line URL editing, the __add()__, __set()__, and __remove()__
methods of furl objects let you manipulate various components of the url and
then return the furl object itself for further use.

    ```python
    >>> url = 'http://www.google.com/#fragment' 
    >>> furl(url).add(args={'example':'arg'}).set(port=99).remove(fragment=True).url
    'http://www.google.com:99/?example=arg'
    ```

__add()__ adds to attributes of a furl object with the optional arguments

 * __args__: Shortcut for __query_params__. See __query_params__ below.
 * __path__: A list of path segments to add to the existing path segments, or a
   path string to join with existing path string.
 * __fragment_path__: A list of path segments to add to the existing fragment
   path segments, or a path string to join with existing fragment path string.
 * __fragment_args__: A dictionary of query keys and values to add to the
   fragment's query.
 * __query_params__: A dictionary of query keys and values to add to the query.

    ```python
    >>> url = 'http://www.google.com/' 
    >>> furl(url).add(path='/index.html', fragment_path='frag/path',
                      fragment_args={'frag':'args'}).url
    'http://www.google.com/index.html#fragment/frag/path?frag=args'
    ```

__set()__ sets attributes of a furl object with the optional arguments

 * __args__: Shortcut for __query_params__. See __query_params__ below.
 * __path__: List of path segments or a path string to adopt.
 * __fragment__: Fragment string to adopt.
 * __scheme__: Scheme string to adopt.
 * __netloc__: Network location string to adopt.
 * __fragment_path__: A list of path segments to adopt for the fragment's path
   or a path string to adopt as the fragment's path.
 * __fragment_args__: A dictionary of query keys and values for the fragment's
   query to adopt.
 * __fragment_separator__: Boolean whether or not there should be a '?'
   separator between the fragment path and fragment query.
 * __host__: Host string to adopt.
 * __port__: Port number to adopt.
 * __query__: Query string to adopt.
 * __query_params__: A dictionary of query keys and values to adopt.

    ```python
    >>> furl().set(scheme='https', host='secure.google.com', port=99,
                   path='index.html', args={'some':'args'}, fragment='great job').url
    'https://secure.google.com:99/index.html?some=args#great job'
    ```

__set()__ removes attributes of a furl object with the optional arguments

 * __args__: Shortcut for __query_params__. See __query_params__ below.
 * __path__: A list of path segments to remove from the end of the existing path
   segments list or a path string to remove from the end of the existing path
   string.
 * __fragment__: If True, remove the fragment portion of the URL entirely.
 * __query__: If True, remove the query portion of the URL entirely.
 * __query_params__: A dictionary of query keys and values to remove from the
   query, if they exist.
 * __port__: If True, remove the port from the network location string, if it
   exists.
 * __fragment_path__: A list of path segments to remove from the end of the
   fragment's path segments or a path string to remove from the end of the
   fragment's path string.
 * __fragment_args__: A dictionary of query keys and values to remove from the
   fragment's query.

    ```python
   >>> url = 'https://secure.google.com:99/a/path/?some=args#great job'
   >>> furl(url).remove(args=['some'], path='path', fragment=True, port=True).url
   'https://secure.google.com/a/'
   ```