# furl

### furl is a small Python library that makes manipulating URLs simple.

Python's standard __urllib__ and __urlparse__ modules provide a number of URL
manipulation functions, but using these functions to perform common URL
manipulations proves tedious. furl makes manipulating URLs simple.

furl is well tested and [Unlicensed](http://unlicense.org/) in the public domain
so you can build amazing things.

Query arguments are easy. Really easy.

```pycon
>>> from furl import furl
>>> f = furl('http://www.google.com/?one=1&two=2')
>>> f.args['three'] = '3'
>>> del f.args['one']
>>> f.url
'http://www.google.com/?two=2&three=3'
```

Or use furl's inline modification methods.

```pycon
>>> furl('http://www.google.com/?one=1').add({'two':'2'}).url
'http://www.google.com/?one=1&two=2'

>>> furl('http://www.google.com/?one=1&two=2').set({'three':'3'}).url
'http://www.google.com/?three=3'

>>> furl('http://www.google.com/?one=1&two=2').remove(['one']).url
'http://www.google.com/?two=2'
```

Encoding is handled for you.

```pycon
>>> f = furl('http://www.google.com/')
>>> f.path = 'some encoding here'
>>> f.args['and some encoding'] = 'here, too'
>>> f.url
'http://www.google.com/some%20encoding%20here?and+some+encoding=here,+too'
```

Fragments have a path and a query, too.

```pycon
>>> f = furl('http://www.google.com/')
>>> f.fragment.path.segments = ['two', 'directories']
>>> f.fragment.args = {'one':'argument'}
>>> f.url
'http://www.google.com/#two/directories?one=argument'
```


### API

See more furl magic and examples in furl's API document,
[API.md](https://github.com/gruns/furl/blob/master/API.md).


### Installation

Installing furl with pip is easy.

```
$ pip install furl
```


### Deprecated methods

__f.pathstr__, __f.querystr__, and __f.fragmentstr__ are deprecated in favor of
`str(f.path)`, `str(f.query)`, and `str(f.fragment)`. There should be one, and
preferably only one, obvious way to serialize URL components to strings.
