# furl API

### Basics

furl objects let you access and modify the components of a URL

```
scheme://username:password@host:port/path?query#fragment
```

 * __scheme__ is the scheme string, all lowercase.
 * __username__ is the username string for authentication.
 * __password__ is the password string for authentication with __username__.
 * __host__ is the domain name, IPv4, or IPv6 address as a string. Domain names
  are all lowercase.
 * __port__ is an integer or None. A value of None means no port specified and
  the default port for the given __scheme__ should be inferred, if possible.
 * __path__ is a Path object comprised of path segments.
 * __query__ is a Query object comprised of query arguments.
 * __fragment__ is a Fragment object comprised of a Path and Query object
   separated by an optional '?' separator.


### Scheme, Username, Password, Host, Port, and Network Location

__scheme__, __username__, __password__, and __host__ are strings. __port__ is an
integer or None.

```pycon
>>> f = furl('http://user:pass@www.google.com:99/')
>>> f.scheme, f.username, f.password, f.host, f.port
('http', 'user', 'pass', 'www.google.com', 99)
```

furl infers the default port for common schemes.

```pycon
>>> f = furl('https://secure.google.com/')
>>> f.port
443

>>> f = furl('unknown://www.google.com/')
>>> print f.port
None
```

__netloc__ is the string combination of __username__, __password__, __host__,
and __port__, not including __port__ if it is None or the default port for the
provided __scheme__.

```pycon
>>> furl('http://www.google.com/').netloc
'www.google.com'

>>> furl('http://www.google.com:99/').netloc
'www.google.com:99'

>>> furl('http://user:pass@www.google.com:99/').netloc
'user:pass@www.google.com:99'
```


### Path

URL paths in furl are Path objects that have __segments__, a list of zero or
more path segments that can be manipulated directly. Path segments in
__segments__ are maintaned decoded and all interaction with __segments__ should
take place with decoded segment strings.

```pycon
>>> f = furl('http://www.google.com/a/larg%20ish/path')
>>> f.path
Path('/a/larg ish/path')
>>> f.path.segments
['a', 'larg ish', 'path']
>>> str(f.path)
'/a/larg%20ish/path'
```

Manipulation

```pycon
>>> f.path.segments = ['a', 'new', 'path', '']
>>> str(f.path)
'/a/new/path/'

>>> f.path = 'o/hi/there/with%20some%20encoding/'
>>> f.path.segments
['o', 'hi', 'there', 'with some encoding', '']
>>> str(f.path)
'/o/hi/there/with%20some%20encoding/'

>>> f.url
'http://www.google.com/o/hi/there/with%20some%20encoding/'

>>> f.path.segments = ['segments', 'are', 'maintained', 'decoded', '^`<>[]"#/?']
>>> str(f.path)
'/segments/are/maintained/decoded/%5E%60%3C%3E%5B%5D%22%23%2F%3F'
```

A path that starts with '/' is considered absolute, and a Path can be absolute
or not as specified (or set) by the boolean attribute __isabsolute__. URL Paths
have a special restriction: they must be absolute if there's a __netloc__
(username, password, host, and/or port) present. This restriction exists because
a URL path must start with '/' to separate itself from a __netloc__. Fragment
Paths have no such limitation and __isabsolute__ and can be be True or False
without restriction.

Here's a URL Path example that illustrates how __isabsolute__ becomes True and
read-only in the presence of a __netloc__.

```pycon
>>> f = furl('/url/path')
>>> f.path.isabsolute
True
>>> f.path.isabsolute = False
>>> f.url
'url/path'
>>> f.host = 'arc.io'
>>> f.url
'arc.io/url/path'
>>> f.path.isabsolute
True
>>> f.path.isabsolute = False
Traceback (most recent call last):
  ...
AttributeError: Path.isabsolute is True and read-only for URLs with a netloc (a username, password, host, and/or port). URL paths must be absolute if a netloc exists.
>>> f.url
'arc.io/url/path'
```

Here's a fragment Path example.

```pycon
>>> f = furl('http://www.google.com/#/absolute/fragment/path/')
>>> f.fragment.path.isabsolute
True
>>> f.fragment.path.isabsolute = False
>>> f.url
'http://www.google.com/#absolute/fragment/path/'
>>> f.fragment.path.isabsolute = True
>>> f.url
'http://www.google.com/#/absolute/fragment/path/'
```

A path that ends with '/' is considered a directory, and otherwise considered a
file. The Path attribute __isdir__ returns True if the path is a directory,
False otherwise. Conversely, the attribute __isfile__ returns True if the path
is a file, False otherwise.

```pycon
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


### Query

URL queries in furl are Query objects that have __params__, a one dimensional
[ordered multivalue dictionary](https://github.com/gruns/orderedmultidict) of
query keys and values. Query keys and values in __params__ are maintained
decoded and all interaction with __params__ should take place with decoded
strings.

```pycon
>>> f = furl('http://www.google.com/?one=1&two=2')
>>> f.query
Query('one=1&two=2')
>>> f.query.params
OneDimensionalOrderedMultidict([('one', '1'), ('two', '2')])
>>> str(f.query)
'one=1&two=2'
```

furl objects and Fragment objects (covered below) contain a Query object, and
__args__ is provided as a shortcut on these objects to access __query.params__.

```pycon
>>> f = furl('http://www.google.com/?one=1&two=2')
>>> f.query.params
OneDimensionalOrderedMultidict([('one', '1'), ('two', '2')])
>>> f.args
OneDimensionalOrderedMultidict([('one', '1'), ('two', '2')])
>>> f.args is f.query.params
True
```

Manipulation

__params__ is a one dimensional
[ordered multivalue dictionary](https://github.com/gruns/orderedmultidict) that
maintains method parity with Python's standard dictionary.

```pycon
>>> f.query = 'silicon=14&iron=26&inexorable%20progress=vae%20victus'
>>> f.query.params
OneDimensionalOrderedMultidict([('silicon', '14'), ('iron', '26'), ('inexorable progress', 'vae victus')])
>>> del f.args['inexorable progress']
>>> f.args['magnesium'] = '12'
>>> f.args
OneDimensionalOrderedMultidict([('silicon', '14'), ('iron', '26'), ('magnesium', '12')])
```

__params__ can also store multiple values for the same key because it is an
[ordered multivalue dictionary](https://github.com/gruns/orderedmultidict).

```pycon
>>> f = furl('http://www.google.com/?space=jams&space=slams')
>>> f.args['space']
'jams'
>>> f.args.getlist('space')
['jams', 'slams']
>>> f.args.addlist('repeated', ['1', '2', '3'])
>>> str(f.query)
'space=jams&space=slams&repeated=1&repeated=2&repeated=3'
>>> f.args.popvalue('space')
'slams'
>>> f.args.popvalue('repeated', '2')
'2'
>>> str(f.query)
'space=jams&repeated=1&repeated=3'
```

__params__ is one dimensional. If a list of values is provided as a query value,
that list is interpretted as multiple values.

```pycon
>>> f = furl()
>>> f.args['repeated'] = ['1', '2', '3']
>>> f.add(args={'space':['jams', 'slams']})
>>> str(f.query)
'repeated=1&repeated=2&repeated=3&space=jams&space=slams'
```

This makes sense -- URL queries are inherently one dimensional. Query values
cannot have subvalues.

See the [omdict](https://github.com/gruns/orderedmultidict) documentation for
more information on interacting with the ordered multivalue dictionary
__params__.


__encode(delimeter='&')__ can be used to encode query strings with delimeters
like `;`.

```pycon
>>> f.query = 'space=jams&woofs=squeeze+dog'
>>> f.query.encode()
'space=jams&woofs=squeeze+dog'
>>> f.query.encode(';')
'space=jams;woofs=squeeze+dog'
```


### Fragment

URL fragments in furl are Fragment objects that have a Path __path__ and Query
__query__ separated by an optional '?' __separator__.

```pycon
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
instances, __path__ and __query__.

```pycon
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
```

Creating hash-bang fragments with furl illustrates the use of Fragment's
__separator__. When __separator__ is False, the '?' separating __path__ and
__query__ isn't included.

```pycon
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
```

### Encoding

furl handles encoding for you, and furl's philosophy on encoding is simple:
whole path, query, and fragment strings should always be encoded.

```pycon
>>> f = furl()
>>> f.path = 'supply%20encoded/whole%20path%20strings'
>>> f.path.segments
['supply encoded', 'whole path strings']

>>> f.set(query='supply+encoded=query+strings,+too')
>>> f.query.params
OneDimensionalOrderedMultidict([('supply encoded', 'query strings, too')])

>>> f.set(fragment='encoded%20path%20string?and+encoded=query+string+too')
>>> f.fragment.path.segments
['encoded path string']
>>> f.fragment.args
OneDimensionalOrderedMultidict([('and encoded', 'query string too')])
```

Path, Query, and Fragment strings should always be decoded.

```pycon
>>> f = furl()
>>> f.set(path=['path segments are', 'decoded', '<>[]"#'])
>>> str(f.path)
'/path%20segments%20are/decoded/%3C%3E%5B%5D%22%23'

>>> f.set(args={'query parameters':'and values', 'are':'decoded, too'})
>>> str(f.query)
'query+parameters=and+values&are=decoded,+too'

>>> f.fragment.path.segments = ['decoded', 'path segments']
>>> f.fragment.args = {'and decoded':'query parameters and values'}
>>> str(f.fragment)
'decoded/path%20segments?and+decoded=query+parameters+and+values'
```

Python's
[urllib.quote()](http://docs.python.org/library/urllib.html#urllib.quote) and
[urllib.unquote()](http://docs.python.org/library/urllib.html#urllib.unquote)
can be used to encode and decode path strings. Similarly,
[urllib.quote_plus()](http://docs.python.org/library/urllib.html#urllib.quote_plus)
and
[urllib.unquote_plus()](http://docs.python.org/library/urllib.html#urllib.unquote_plus)
can be used to encode and decode query strings.


### Inline manipulation

For quick, single-line URL manipulation, the __add()__, __set()__, and
__remove()__ methods of furl objects manipulate various components of the URL
and return the furl object for method chaining.

```pycon
>>> url = 'http://www.google.com/#fragment' 
>>> furl(url).add(args={'example':'arg'}).set(port=99).remove(fragment=True).url
'http://www.google.com:99/?example=arg'
```

__add()__ adds items to a furl object with the optional arguments

 * __args__: Shortcut for __query_params__.
 * __path__: A list of path segments to add to the existing path segments, or a
   path string to join with the existing path string.
 * __query_params__: A dictionary of query keys and values to add to the query.
 * __fragment_path__: A list of path segments to add to the existing fragment
   path segments, or a path string to join with the existing fragment path
   string.
 * __fragment_args__: A dictionary of query keys and values to add to the
   fragment's query.

```pycon
>>> url = 'http://www.google.com/' 
>>> furl(url).add(path='/index.html', fragment_path='frag/path',
                  fragment_args={'frag':'args'}).url
'http://www.google.com/index.html#frag/path?frag=args'
```

__set()__ sets items of a furl object with the optional arguments

 * __args__: Shortcut for __query_params__.
 * __path__: List of path segments or a path string to adopt.
 * __scheme__: Scheme string to adopt.
 * __netloc__: Network location string to adopt.
 * __query__: Query string to adopt.
 * __query_params__: A dictionary of query keys and values to adopt.
 * __fragment__: Fragment string to adopt.
 * __fragment_path__: A list of path segments to adopt for the fragment's path
   or a path string to adopt as the fragment's path.
 * __fragment_args__: A dictionary of query keys and values for the fragment's
   query to adopt.
 * __fragment_separator__: Boolean whether or not there should be a '?'
   separator between the fragment path and the fragment query.
 * __host__: Host string to adopt.
 * __port__: Port number to adopt.
 * __username__: Username string to adopt.
 * __password__: password string to adopt.


```pycon
>>> furl().set(scheme='https', host='secure.google.com', port=99,
               path='index.html', args={'some':'args'}, fragment='great job').url
'https://secure.google.com:99/index.html?some=args#great%20job'
```

__remove()__ removes items from a furl object with the optional arguments

 * __args__: Shortcut for __query_params__.
 * __path__: A list of path segments to remove from the end of the existing path
        segments list, or a path string to remove from the end of the existing
        path string, or True to remove the path entirely.
 * __fragment__: If True, remove the fragment portion of the URL entirely.
 * __query__: If True, remove the query portion of the URL entirely.
 * __query_params__: A list of query keys to remove from the query, if they
        exist.
 * __port__: If True, remove the port from the network location string, if it
   exists.
 * __fragment_path__: A list of path segments to remove from the end of the
   fragment's path segments, or a path string to remove from the end of the
   fragment's path string, or True to remove the fragment path entirely.
 * __fragment_args__: A list of query keys to remove from the fragment's query,
   if they exist.
 * __username__: If True, remove the username, if it exists.
 * __password__: If True, remove the password, if it exists.


```pycon
>>> url = 'https://secure.google.com:99/a/path/?some=args#great job'
>>> furl(url).remove(args=['some'], path='path/', fragment=True, port=True).url
'https://secure.google.com/a/'
```


### Miscellaneous

__copy()__ creates and returns a new furl object with an identical URL.

```pycon
>>> f = furl('http://www.google.com')
>>> f.copy().set(path='/new/path').url
'http://www.google.com/new/path'
>>> f.url
'http://www.google.com'
```

__join()__ joins the furl object's URL with the provided relative or absolute
URL and returns the furl object for method chaining. __join()__'s action is the
same as clicking on the provided relative or absolute URL in a browser.

```pycon
>>> f = furl('http://www.google.com')
>>> f.join('new/path').url
'http://www.google.com/new/path'
>>> f.join('replaced').url
'http://www.google.com/new/replaced'
>>> f.join('../parent').url
'http://www.google.com/parent'
>>> f.join('path?query=yes#fragment').url
'http://www.google.com/path?query=yes#fragment'
>>> f.join('unknown://www.yahoo.com/new/url/').url
'unknown://www.yahoo.com/new/url/'
```
