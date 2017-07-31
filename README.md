<h1 align="center">
  <img src="https://cdn.rawgit.com/gruns/furl/1162fce0abc5b349ff5f75c0e24a42504f426dc2/logo.svg" width="300px" alt="furl">
</h1>

<p align="center">
  <a href="https://pypi.python.org/pypi/furl">
    <img src="https://badge.fury.io/py/furl.svg">
  </a>
  <a href="https://travis-ci.org/gruns/furl">
    <img src="https://img.shields.io/travis/gruns/furl.svg">
  </a>
  <a href="http://unlicense.org/">
    <img src="https://img.shields.io/pypi/l/furl.svg">
  </a>
  <a href="https://pypi.python.org/pypi/furl">
    <img src="https://img.shields.io/pypi/pyversions/furl.svg">
  </a>
</p>

### furl is a small Python library that makes parsing and manipulating URLs easy.

Python's standard [urllib](https://docs.python.org/2/library/urllib.html) and
[urlparse](https://docs.python.org/2/library/urlparse.html) modules provide a
number of URL\
related functions, but using these functions to perform common
URL\
operations proves tedious. Furl makes parsing and manipulating URLs\
easy.

Furl is well tested, [Unlicensed](http://unlicense.org/) in the public domain,
and supports\
Python 2, Python 3, PyPy2, and PyPy3.

Code time: Query arguments are easy. Really easy.

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

Encoding is handled for you. Unicode, too.

```python
>>> f = furl('http://www.google.com/')
>>> f.path = 'some encoding here'
>>> f.args['and some encoding'] = 'here, too'
>>> f.url
'http://www.google.com/some%20encoding%20here?and+some+encoding=here,+too'
>>> f.set(host=u'ドメイン.テスト', path=u'джк', query=u'☃=☺')
>>> f.url
'http://xn--eckwd4c7c.xn--zckzah/%D0%B4%D0%B6%D0%BA?%E2%98%83=%E2%98%BA'
```

Fragments also have a path and a query.

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
