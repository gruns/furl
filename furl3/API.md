# furl API

***
### Basics

furl objects let you access and modify the components of a URL

```
scheme://username:password@host:port/path?query#fragment
```

 * `scheme` is the scheme string, all lowercase.
 * `username` is the username string for authentication.
 * `password` is the password string for authentication with `username`.
 * `host` is the domain name, IPv4, or IPv6 address as a string. Domain names
  are all lowercase.
 * `port` is an integer or None. A value of None means no port specified and
  the default port for the given `scheme` should be inferred, if possible.
 * `path` is a Path object comprised of path segments.
 * `query` is a Query object comprised of query arguments.
 * `fragment` is a Fragment object comprised of a Path and Query object
   separated by an optional '?' separator.


***
### Scheme, Username, Password, Host, Port, and Network Location

`scheme`, `username`, `password`, and `host` are strings. `port` is an
integer or None.

    >>> from furl import furl
    >>> f = furl('http://user:pass@www.google.com:99/')
    >>> f.scheme, f.username, f.password, f.host, f.port
    ('http', 'user', 'pass', 'www.google.com', 99)

furl infers the default port for common schemes

    >>> f = furl('https://secure.google.com/')
    >>> f.port
    443
    >>> f = furl('unknown://www.google.com/')
    >>> print(f.port)
    None


`netloc` is the string combination of `username`, `password`, `host`,
and `port`, not including `port` if it is None or the default port for the
provided `scheme`.

    >>> furl('http://www.google.com/').netloc
    'www.google.com'
    >>> furl('http://www.google.com:99/').netloc
    'www.google.com:99'
    >>> furl('http://user:pass@www.google.com:99/').netloc
    'user:pass@www.google.com:99'

***
### Path

URL paths are Path objects in furl, and are composed of zero or more path
`segments` that can be manipulated directly. `segments` are maintaned URL
decoded.

    >>> f = furl('http://www.google.com/a/larg%20ish/path')
    >>> f.path
    Path('/a/larg ish/path')
    >>> f.path.segments
    ['a', 'larg ish', 'path']
    >>> str(f.path)
    '/a/larg ish/path'

Manipulation

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

A Path can be absolute or not, as specified by the boolean `isabsolute`. While
URL paths are always absolute if they aren't empty, `isabsolute` is useful for
fragment paths.

    >>> f = furl('http://www.google.com/a/directory/#/absolute/fragment/path/')
    >>> f.path.isabsolute
    True
    >>> f.fragment.path.isabsolute
    True
    >>> f.fragment.path.isabsolute = False
    >>> f.url
    'http://www.google.com/a/directory/#absolute/fragment/path/'

A path that ends with '/' is considered a directory, and otherwise considered a
file. The Path attribute `isdir` returns True if the path is a directory,
False otherwise. Conversely, the attribute `isfile` returns True if the path
is a file, False otherwise.

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


***
### Query

URL queries are Query objects in furl, and are composed of a dictionary of query
keys and values, `params`. Query keys and values in `params` are maintained
unquoted.

    >>> f = furl('http://www.google.com/?one=1&two=2')
    >>> f.query
    Query('two=2&one=1')
    >>> f.query.params
    {'two': '2', 'one': '1'}
    >>> str(f.query)
    'two=2&one=1'

Manipulation

    >>> f.query = 'three=3&four=4'
    >>> f.query.params
    {'four': '4', 'three': '3'}
    >>> f.query.params['five'] = '5'
    >>> del f.query.params['three']
    >>> f.query.params
    {'four': '4', 'five': '5'}


Both furl objects and Fragment objects (covered below) contain a Query instance,
and `args` is provided as a shortcut on these objects to access
`query.params`.

    >>> f = furl('http://www.google.com/?one=1&two=2')
    >>> f.args
    {'two': '2', 'one': '1'}
    >>> f.query.params
    {'two': '2', 'one': '1'}
    >>> f.args == f.query.params
    True


***
### Fragment

URL fragments are Fragment objects in furl, and are composed of a `path` and
`query` separated by an optional '?' `separator`.

    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> f.fragment
    Fragment('/fragment/path?with=params')
    >>> f.fragment.path
    Path('/fragment/path')
    >>> f.fragment.query
    Query('with=params')
    >>> f.fragment.separator
    True

Manipulation of Fragments is done through the Fragment's Path and Query
instances.

    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> str(f.fragment)
    '/fragment/path?with=params'
    >>> f.fragment.path.segments.append('file.ext')
    >>> str(f.fragment)
    '/fragment/path/file.ext?with=params'

    >>> f = furl('http://www.google.com/#/fragment/path?with=params')
    >>> str(f.fragment)
    '/fragment/path?with=params'
    >>> f.fragment.args['new'] = 'yep'
    >>> str(f.fragment)
    '/fragment/path?new=yep&with=params'

Creating hash-bang fragments with furl illustrates the use of Fragment's
`separator`. When `separator` is False, the '?' separating the Fragment's
Path and Query isn't included.

    >>> f = furl('http://www.google.com/')
    >>> f.fragment.path = '!'
    >>> f.fragment.args = {'a':'dict', 'of':'args'}
    >>> f.fragment.separator
    True
    >>> str(f.fragment)
    '!?a=dict&of=args'

    >>> f.fragment.separator = False
    >>> str(f.fragment)
    '!a=dict&of=args'
    >>> f.url
    'http://www.google.com/#!a=dict&of=args'

***
### Inline modification

For quick, single-line URL editing, the `add()`, `set()`, and `remove()`
methods of furl objects let you manipulate various components of the url and
return the furl object itself for further use.

    >>> url = 'http://www.google.com/#fragment' 
    >>> furl(url).add(args={'example':'arg'}).set(port=99).remove(fragment=True).url
    'http://www.google.com:99/?example=arg'

`add()` adds items to a furl object with the optional arguments

 * `args`: Shortcut for `query_params`.
 * `path`: A list of path segments to add to the existing path segments, or a
   path string to join with the existing path string.
 * `query_params`: A dictionary of query keys and values to add to the query.
 * `fragment_path`: A list of path segments to add to the existing fragment
   path segments, or a path string to join with the existing fragment path
   string.
 * `fragment_args`: A dictionary of query keys and values to add to the
   fragment's query.

    >>> url = 'http://www.google.com/'
    >>> furl(url).add(path='/index.html', fragment_path='frag/path',
    ...               fragment_args={'frag':'args'}).url
    'http://www.google.com/index.html#frag/path?frag=args'

`set()` sets items of a furl object with the optional arguments

 * `args`: Shortcut for `query_params`.
 * `path`: List of path segments or a path string to adopt.
 * `scheme`: Scheme string to adopt.
 * `netloc`: Network location string to adopt.
 * `query`: Query string to adopt.
 * `query_params`: A dictionary of query keys and values to adopt.
 * `fragment`: Fragment string to adopt.
 * `fragment_path`: A list of path segments to adopt for the fragment's path
   or a path string to adopt as the fragment's path.
 * `fragment_args`: A dictionary of query keys and values for the fragment's
   query to adopt.
 * `fragment_separator`: Boolean whether or not there should be a '?'
   separator between the fragment path and the fragment query.
 * `host`: Host string to adopt.
 * `port`: Port number to adopt.
 * `username`: Username string to adopt.
 * `password`: password string to adopt.


    >>> furl().set(scheme='https', host='secure.google.com', port=99,
    ...            path='index.html', args={'some':'args'}, fragment='great job').url
    'https://secure.google.com:99/index.html?some=args#great job'

`remove()` removes items from a furl object with the optional arguments

 * `args`: Shortcut for `query_params`.
 * `path`: A list of path segments to remove from the end of the existing path
        segments list, or a path string to remove from the end of the existing
        path string, or True to remove the path entirely.
 * `fragment`: If True, remove the fragment portion of the URL entirely.
 * `query`: If True, remove the query portion of the URL entirely.
 * `query_params`: A list of query keys to remove from the query, if they
        exist.
 * `port`: If True, remove the port from the network location string, if it
   exists.
 * `fragment_path`: A list of path segments to remove from the end of the
   fragment's path segments or a path string to remove from the end of the
   fragment's path string.
 * `fragment_args`: A list of query keys to remove from the fragment's query,
   if they exist.
 * `username`: If True, remove the username, if it exists.
 * `password`: If True, remove the password, if it exists.


    >>> url = 'https://secure.google.com:99/a/path/?some=args#great job'
    >>> furl(url).remove(args=['some'], path='path', fragment=True, port=True).url
    'https://secure.google.com/a/'
