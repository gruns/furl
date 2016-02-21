# furl
[![Badge fury](https://badge.fury.io/py/furl.svg)](https://pypi.python.org/pypi/furl)
[![Build status](https://api.travis-ci.org/gruns/furl.svg)](https://travis-ci.org/gruns/furl)

### furl is a small Python library that makes manipulating URLs simple.

Python's standard __urllib__ and __urlparse__ modules provide a number of URL
manipulation functions, but using these functions to perform common URL
manipulations proves tedious. Furl makes manipulating URLs easy.

Furl is well tested, [Unlicensed](http://unlicense.org/) in the public domain,
and supports both Python 2 and 3.

Query arguments are easy. Really easy.

```python
>>> from furl import furl
>>> f = furl('http://www.google.com/?one=1&two=2')
>>> f.args['three'] = '3'
>>> del f.args['one']
>>> f.url
'http://www.google.com/?two=2&three=3'
```

Or use furl's inline modification methods.

```python
>>> furl('http://www.google.com/?one=1').add({'two':'2'}).url
'http://www.google.com/?one=1&two=2'

>>> furl('http://www.google.com/?one=1&two=2').set({'three':'3'}).url
'http://www.google.com/?three=3'

>>> furl('http://www.google.com/?one=1&two=2').remove(['one']).url
'http://www.google.com/?two=2'
```

Encoding is handled for you.

```python
>>> f = furl('http://www.google.com/')
>>> f.path = 'some encoding here'
>>> f.args['and some encoding'] = 'here, too'
>>> f.url
'http://www.google.com/some%20encoding%20here?and+some+encoding=here,+too'
```

Fragments have a path and a query, too.

```python
>>> f = furl('http://www.google.com/')
>>> f.fragment.path.segments = ['two', 'directories']
>>> f.fragment.args = {'one':'argument'}
>>> f.url
'http://www.google.com/#two/directories?one=argument'
```

Or get fancy.

```python
>>> f = furl('http://www.google.com/search?q=query#1')
>>> f.copy().remove(path=True).set(host='taco.com')
...  .join('/pumps.html').add(fragment_path='party').url
'http://taco.com/pumps.html#party'
```


### API

See more furl magic and examples in furl's API document,
[API.md](https://github.com/gruns/furl/blob/master/API.md).


### Installation

Installing furl with pip is easy.

```
$ pip install furl
```
