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
import urllib
if sys.version_info[0] >= 2 and sys.version_info[1] >= 7:
    import unittest
else:
    import unittest2 as unittest
import urlparse
import warnings
from itertools import izip
from abc import ABCMeta, abstractmethod
try:
    from collections import OrderedDict as odict  # Python 2.7+.
except ImportError:
    from ordereddict import OrderedDict as odict  # Python 2.4-2.6.

import furl
from furl.omdict1D import omdict1D

PYTHON_27PLUS = sys.version_info[0] >= 2 and sys.version_info[1] >= 7

#
# TODO(grun): Add tests for furl objects with strict=True. Make sure
# UserWarnings are raised when improperly encoded path, query, and
# fragment strings are provided.
#


class itemcontainer(object):

    """
    Utility list subclasses to expose allitems() and iterallitems()
    methods on different kinds of item containers - lists, dictionaries,
    multivalue dictionaries, and query strings. This provides a common
    iteration interface for looping through their items (including items
    with repeated keys).  original() is also provided to get access to a
    copy of the original container.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def allitems(self):
        pass

    @abstractmethod
    def iterallitems(self):
        pass

    @abstractmethod
    def original(self):
        """
        Returns: A copy of the original data type. For example, an
        itemlist would return a list, itemdict a dict, etc.
        """
        pass


class itemlist(list, itemcontainer):

    def allitems(self):
        return list(self.iterallitems())

    def iterallitems(self):
        return iter(self)

    def original(self):
        return list(self)


class itemdict(odict, itemcontainer):

    def allitems(self):
        return self.items()

    def iterallitems(self):
        return self.iteritems()

    def original(self):
        return dict(self)


class itemomdict1D(omdict1D, itemcontainer):

    def original(self):
        return omdict1D(self)


class itemstr(str, itemcontainer):

    def allitems(self):
        # Keys and values get unquoted. i.e. 'a=a%20a' -> ['a', 'a a']. Empty
        # values without '=' have value None.
        items = []
        parsed = urlparse.parse_qsl(self, keep_blank_values=True)
        pairstrs = pairstrs = [s2 for s1 in self.split('&')
                               for s2 in s1.split(';')]
        for (key, value), pairstr in zip(parsed, pairstrs):
            if key == urllib.quote_plus(pairstr):
                value = None
            items.append((key, value))
        return items

    def iterallitems(self):
        return iter(self.allitems())

    def original(self):
        return str(self)


class TestPath(unittest.TestCase):

    def test_isdir_isfile(self):
        for path in ['', '/']:
            p = furl.Path(path)
            assert p.isdir
            assert not p.isfile

        paths = ['dir1/', 'd1/d2/', 'd/d/d/d/d/', '/', '/dir1/', '/d1/d2/d3/']
        for path in paths:
            p = furl.Path(path)
            assert p.isdir
            assert not p.isfile

        for path in ['dir1', 'd1/d2', 'd/d/d/d/d', '/dir1', '/d1/d2/d3']:
            p = furl.Path(path)
            assert p.isfile
            assert not p.isdir

    def test_leading_slash(self):
        p = furl.Path('')
        assert not p.isabsolute
        assert not p.segments
        assert p.isdir and p.isdir != p.isfile
        assert str(p) == ''

        p = furl.Path('/')
        assert p.isabsolute
        assert p.segments == ['']
        assert p.isdir and p.isdir != p.isfile
        assert str(p) == '/'

        p = furl.Path('sup')
        assert not p.isabsolute
        assert p.segments == ['sup']
        assert p.isfile and p.isdir != p.isfile
        assert str(p) == 'sup'

        p = furl.Path('/sup')
        assert p.isabsolute
        assert p.segments == ['sup']
        assert p.isfile and p.isdir != p.isfile
        assert str(p) == '/sup'

        p = furl.Path('a/b/c')
        assert not p.isabsolute
        assert p.segments == ['a', 'b', 'c']
        assert p.isfile and p.isdir != p.isfile
        assert str(p) == 'a/b/c'

        p = furl.Path('/a/b/c')
        assert p.isabsolute
        assert p.segments == ['a', 'b', 'c']
        assert p.isfile and p.isdir != p.isfile
        assert str(p) == '/a/b/c'

        p = furl.Path('a/b/c/')
        assert not p.isabsolute
        assert p.segments == ['a', 'b', 'c', '']
        assert p.isdir and p.isdir != p.isfile
        assert str(p) == 'a/b/c/'

        p.isabsolute = True
        assert p.isabsolute
        assert str(p) == '/a/b/c/'

    def test_encoding(self):
        encoded = ['a%20a', '/%7haypepps/', 'a/:@/a', 'a%2Fb']
        unencoded = ['a+a', '/~haypepps/', 'a/:@/a', 'a/b']

        for path in encoded:
            assert str(furl.Path(path)) == path

        for path in unencoded:
            assert str(furl.Path(path)) == urllib.quote(
                path, "/:@-._~!$&'()*+,;=")

        # Valid path segment characters should not be encoded.
        for char in ":@-._~!$&'()*+,;=":
            f = furl.furl().set(path=char)
            assert str(f.path) == f.url == char
            assert f.path.segments == [char]

        # Invalid path segment characters should be encoded.
        for char in ' ^`<>[]"?':
            f = furl.furl().set(path=char)
            assert str(f.path) == f.url == urllib.quote(char)
            assert f.path.segments == [char]

        # Encode '/' within a path segment.
        segment = 'a/b'  # One path segment that includes the '/' character.
        f = furl.furl().set(path=[segment])
        assert str(f.path) == 'a%2Fb'
        assert f.path.segments == [segment]
        assert f.url == 'a%2Fb'

    def test_load(self):
        self._test_set_load(furl.Path.load)

    def test_set(self):
        self._test_set_load(furl.Path.set)

    def _test_set_load(self, path_set_or_load):
        p = furl.Path('a/b/c/')
        assert path_set_or_load(p, 'asdf/asdf/') == p
        assert not p.isabsolute
        assert str(p) == 'asdf/asdf/'
        assert path_set_or_load(p, ['a', 'b', 'c', '']) == p
        assert not p.isabsolute
        assert str(p) == 'a/b/c/'
        assert path_set_or_load(p, ['', 'a', 'b', 'c', '']) == p
        assert p.isabsolute
        assert str(p) == '/a/b/c/'

    def test_add(self):
        # URL paths.
        p = furl.furl('a/b/c/').path
        assert p.add('d') == p
        assert not p.isabsolute
        assert str(p) == 'a/b/c/d'
        assert p.add('/') == p
        assert not p.isabsolute
        assert str(p) == 'a/b/c/d/'
        assert p.add(['e', 'f', 'e e', '']) == p
        assert not p.isabsolute
        assert str(p) == 'a/b/c/d/e/f/e%20e/'

        p = furl.furl().path
        assert not p.isabsolute
        assert p.add('/') == p
        assert p.isabsolute
        assert str(p) == '/'
        assert p.add('pump') == p
        assert p.isabsolute
        assert str(p) == '/pump'

        p = furl.furl().path
        assert not p.isabsolute
        assert p.add(['', '']) == p
        assert p.isabsolute
        assert str(p) == '/'
        assert p.add(['pump', 'dump', '']) == p
        assert p.isabsolute
        assert str(p) == '/pump/dump/'

        p = furl.furl('http://sprop.ru/a/b/c/').path
        assert p.add('d') == p
        assert p.isabsolute
        assert str(p) == '/a/b/c/d'
        assert p.add('/') == p
        assert p.isabsolute
        assert str(p) == '/a/b/c/d/'
        assert p.add(['e', 'f', 'e e', '']) == p
        assert p.isabsolute
        assert str(p) == '/a/b/c/d/e/f/e%20e/'

        f = furl.furl('http://sprop.ru')
        assert not f.path.isabsolute
        f.path.add('sup')
        assert f.path.isabsolute and str(f.path) == '/sup'

        f = furl.furl('/mrp').add(path='sup')
        assert str(f.path) == '/mrp/sup'

        f = furl.furl('/').add(path='/sup')
        assert f.path.isabsolute and str(f.path) == '/sup'

        f = furl.furl('/hi').add(path='sup')
        assert f.path.isabsolute and str(f.path) == '/hi/sup'

        f = furl.furl('/hi').add(path='/sup')
        assert f.path.isabsolute and str(f.path) == '/hi/sup'

        f = furl.furl('/hi/').add(path='/sup')
        assert f.path.isabsolute and str(f.path) == '/hi//sup'

        # Fragment paths.
        f = furl.furl('http://sprop.ru#mrp')
        assert not f.fragment.path.isabsolute
        f.fragment.path.add('sup')
        assert not f.fragment.path.isabsolute
        assert str(f.fragment.path) == 'mrp/sup'

        f = furl.furl('http://sprop.ru#/mrp')
        assert f.fragment.path.isabsolute
        f.fragment.path.add('sup')
        assert f.fragment.path.isabsolute
        assert str(f.fragment.path) == '/mrp/sup'

    def test_remove(self):
        # Remove lists of path segments.
        p = furl.Path('a/b/s%20s/')
        assert p.remove(['b', 's s']) == p
        assert str(p) == 'a/b/s%20s/'
        assert p.remove(['b', 's s', '']) == p
        assert str(p) == 'a/'
        assert p.remove(['', 'a']) == p
        assert str(p) == 'a/'
        assert p.remove(['a']) == p
        assert str(p) == 'a/'
        assert p.remove(['a', '']) == p
        assert str(p) == ''

        p = furl.Path('a/b/s%20s/')
        assert p.remove(['', 'b', 's s']) == p
        assert str(p) == 'a/b/s%20s/'
        assert p.remove(['', 'b', 's s', '']) == p
        assert str(p) == 'a'
        assert p.remove(['', 'a']) == p
        assert str(p) == 'a'
        assert p.remove(['a', '']) == p
        assert str(p) == 'a'
        assert p.remove(['a']) == p
        assert str(p) == ''

        p = furl.Path('a/b/s%20s/')
        assert p.remove(['a', 'b', 's%20s', '']) == p
        assert str(p) == 'a/b/s%20s/'
        assert p.remove(['a', 'b', 's s', '']) == p
        assert str(p) == ''

        # Remove a path string.
        p = furl.Path('a/b/s%20s/')
        assert p.remove('b/s s/') == p  # Encoding Warning.
        assert str(p) == 'a/'

        p = furl.Path('a/b/s%20s/')
        assert p.remove('b/s%20s/') == p
        assert str(p) == 'a/'
        assert p.remove('a') == p
        assert str(p) == 'a/'
        assert p.remove('/a') == p
        assert str(p) == 'a/'
        assert p.remove('a/') == p
        assert str(p) == ''

        p = furl.Path('a/b/s%20s/')
        assert p.remove('b/s s') == p  # Encoding Warning.
        assert str(p) == 'a/b/s%20s/'

        p = furl.Path('a/b/s%20s/')
        assert p.remove('b/s%20s') == p
        assert str(p) == 'a/b/s%20s/'
        assert p.remove('s%20s') == p
        assert str(p) == 'a/b/s%20s/'
        assert p.remove('s s') == p  # Encoding Warning.
        assert str(p) == 'a/b/s%20s/'
        assert p.remove('b/s%20s/') == p
        assert str(p) == 'a/'
        assert p.remove('/a') == p
        assert str(p) == 'a/'
        assert p.remove('a') == p
        assert str(p) == 'a/'
        assert p.remove('a/') == p
        assert str(p) == ''

        p = furl.Path('a/b/s%20s/')
        assert p.remove('a/b/s s/') == p  # Encoding Warning.
        assert str(p) == ''

        # Remove True.
        p = furl.Path('a/b/s%20s/')
        assert p.remove(True) == p
        assert str(p) == ''

    def test_isabsolute(self):
        paths = ['', '/', 'pump', 'pump/dump', '/pump/dump', '/pump/dump']
        for path in paths:
            # A URL path's isabsolute attribute is mutable if there's no
            # netloc.
            mutable = [
                {},  # No scheme or netloc -> isabsolute is mutable.
                {'scheme': 'nonempty'}]  # Scheme, no netloc -> isabs mutable.
            for kwargs in mutable:
                f = furl.furl().set(path=path, **kwargs)
                if path and path.startswith('/'):
                    assert f.path.isabsolute
                else:
                    assert not f.path.isabsolute
                f.path.isabsolute = False  # No exception.
                assert not f.path.isabsolute and not str(
                    f.path).startswith('/')
                f.path.isabsolute = True  # No exception.
                assert f.path.isabsolute and str(f.path).startswith('/')

            # A URL path's isabsolute attribute is read-only if there's
            # a netloc.
            readonly = [
                # Netloc, no scheme -> isabsolute is read-only if path
                # is non-empty.
                {'netloc': 'nonempty'},
                # Netloc and scheme -> isabsolute is read-only if path
                # is non-empty.
                {'scheme': 'nonempty', 'netloc': 'nonempty'}]
            for kwargs in readonly:
                f = furl.furl().set(path=path, **kwargs)
                if path:  # Exception raised.
                    with self.assertRaises(AttributeError):
                        f.path.isabsolute = False
                    with self.assertRaises(AttributeError):
                        f.path.isabsolute = True
                else:  # No exception raised.
                    f.path.isabsolute = False
                    assert not f.path.isabsolute and not str(
                        f.path).startswith('/')
                    f.path.isabsolute = True
                    assert f.path.isabsolute and str(f.path).startswith('/')

            # A Fragment path's isabsolute attribute is never read-only.
            f = furl.furl().set(fragment_path=path)
            if path and path.startswith('/'):
                assert f.fragment.path.isabsolute
            else:
                assert not f.fragment.path.isabsolute
            f.fragment.path.isabsolute = False  # No exception.
            assert (not f.fragment.path.isabsolute and
                    not str(f.fragment.path).startswith('/'))
            f.fragment.path.isabsolute = True  # No exception.
            assert f.fragment.path.isabsolute and str(
                f.fragment.path).startswith('/')

            # Sanity checks.
            f = furl.furl().set(scheme='mailto', path='dad@pumps.biz')
            assert str(f) == 'mailto:dad@pumps.biz' and not f.path.isabsolute
            f.path.isabsolute = True  # No exception.
            assert str(f) == 'mailto:/dad@pumps.biz' and f.path.isabsolute

            f = furl.furl().set(scheme='sup', fragment_path='/dad@pumps.biz')
            assert str(
                f) == 'sup:#/dad@pumps.biz' and f.fragment.path.isabsolute
            f.fragment.path.isabsolute = False  # No exception.
            assert str(
                f) == 'sup:#dad@pumps.biz' and not f.fragment.path.isabsolute

    def test_normalize(self):
        # Path not modified.
        for path in ['', 'a', '/a', '/a/', '/a/b%20b/c', '/a/b%20b/c/']:
            p = furl.Path(path)
            assert p.normalize() is p and str(p) == str(p.normalize()) == path

        # Path modified.
        tonormalize = [
            ('//', '/'), ('//a', '/a'), ('//a/', '/a/'), ('//a///', '/a/'),
            ('////a/..//b', '/b'), ('/a/..//b//./', '/b/')]
        for path, normalized in tonormalize:
            p = furl.Path(path)
            assert p.normalize() is p and str(p.normalize()) == normalized

    def test_nonzero(self):
        p = furl.Path()
        assert not p

        p = furl.Path('')
        assert not p

        p = furl.Path('')
        assert not p
        p.segments = ['']
        assert p

        p = furl.Path('asdf')
        assert p

        p = furl.Path('/asdf')
        assert p


class TestQuery(unittest.TestCase):

    def setUp(self):
        # All interaction with parameters is unquoted unless that
        # interaction is through an already encoded query string. In the
        # case of an already encoded query string like 'a=a%20a&b=b',
        # its keys and values will be unquoted.
        self.itemlists = map(itemlist, [
            [], [(1, 1)], [(1, 1), (2, 2)], [
                (1, 1), (1, 11), (2, 2), (3, 3)], [('', '')],
            [('a', 1), ('b', 2), ('a', 3)], [
                ('a', 1), ('b', 'b'), ('a', 0.23)],
            [(0.1, -0.9), (-0.1231, 12312.3123)], [
                (None, None), (None, 'pumps')],
            [('', ''), ('', '')], [('', 'a'), ('', 'b'),
                                   ('b', ''), ('b', 'b')], [('<', '>')],
            [('=', '><^%'), ('><^%', '=')], [
                ("/?:@-._~!$'()*+,", "/?:@-._~!$'()*+,=")],
            [('+', '-')], [('a%20a', 'a%20a')], [('/^`<>[]"', '/^`<>[]"=')],
            [("/?:@-._~!$'()*+,", "/?:@-._~!$'()*+,=")],
        ])
        self.itemdicts = map(itemdict, [
            {}, {1: 1, 2: 2}, {'1': '1', '2': '2',
                               '3': '3'}, {None: None}, {5.4: 4.5},
            {'': ''}, {'': 'a', 'b': ''}, {
                'pue': 'pue', 'a': 'a&a'}, {'=': '====='},
            {'pue': 'pue', 'a': 'a%26a'}, {'%': '`', '`': '%'}, {'+': '-'},
            {"/?:@-._~!$'()*+,": "/?:@-._~!$'()*+,="}, {
                '%25': '%25', '%60': '%60'},
        ])
        self.itemomdicts = map(itemomdict1D, self.itemlists)
        self.itemstrs = map(itemstr, [
            # Basics.
            '', 'a=a', 'a=a&b=b', 'q=asdf&check_keywords=yes&area=default',
            '=asdf',
            # Various quoted and unquoted parameters and values that
            # will be unquoted.
            'space=a+a&amp=a%26a', 'a a=a a&no encoding=sup', 'a+a=a+a',
            'a%20=a+a', 'a%20a=a%20a', 'a+a=a%20a', 'space=a a&amp=a^a',
            'a=a&s=s#s', '+=+', "/?:@-._~!$&'()*+,=/?:@-._~!$'()*+,=",
            'a=a&c=c%5Ec', '<=>&^="', '%3C=%3E&%5E=%22', '%=%;`=`',
            '%25=%25&%60=%60',
            # Only keys, no values.
            'asdfasdf', '/asdf/asdf/sdf', '*******', '!@#(*&@!#(*@!#', 'a&b&',
            'a;b',
            # Repeated parameters.
            'a=a&a=a', 'space=a+a&space=b+b',
            # Empty keys and/or values.
            '=', 'a=', 'a=a&a=', '=a&=b',
            # Semicolon delimeter, like 'a=a;b=b'.
            'a=a;a=a', 'space=a+a;space=b+b',
        ])
        self.items = (self.itemlists + self.itemdicts + self.itemomdicts +
                      self.itemstrs)

    def test_various(self):
        for items in self.items:
            q = furl.Query(items.original())
            assert q.params.allitems() == items.allitems()
            pairs = map(lambda pair: '%s=%s' % (pair[0], pair[1]),
                        self._quote_items(items))

            # encode() and __str__().
            assert str(q) == q.encode() == q.encode('&')

            # __nonzero__().
            if items.allitems():
                assert q
            else:
                assert not q

    def test_load(self):
        for items in self.items:
            q = furl.Query(items.original())
            for update in self.items:
                assert q.load(update) == q
                assert q.params.allitems() == update.allitems()

    def test_add(self):
        for items in self.items:
            q = furl.Query(items.original())
            runningsum = list(items.allitems())
            for itemupdate in self.items:
                assert q.add(itemupdate.original()) == q
                for item in itemupdate.iterallitems():
                    runningsum.append(item)
                assert q.params.allitems() == runningsum

    def test_set(self):
        for items in self.items:
            q = furl.Query(items.original())
            items_omd = omdict1D(items.allitems())
            for update in self.items:
                q.set(update)
                items_omd.updateall(update)
                assert q.params.allitems() == items_omd.allitems()

        # The examples.
        q = furl.Query({1: 1}).set([(1, None), (2, 2)])
        assert q.params.allitems() == [(1, None), (2, 2)]

        q = furl.Query({1: None, 2: None}).set([(1, 1), (2, 2), (1, 11)])
        assert q.params.allitems() == [(1, 1), (2, 2), (1, 11)]

        q = furl.Query({1: None}).set([(1, [1, 11, 111])])
        assert q.params.allitems() == [(1, 1), (1, 11), (1, 111)]

        # Further manual tests.
        q = furl.Query([(2, None), (3, None), (1, None)])
        q.set([(1, [1, 11]), (2, 2), (3, [3, 33])])
        assert q.params.allitems() == [
            (2, 2), (3, 3), (1, 1), (1, 11), (3, 33)]

    def test_remove(self):
        for items in self.items:
            # Remove one key at a time.
            q = furl.Query(items.original())
            for key in dict(items.iterallitems()):
                assert key in q.params
                assert q.remove(key) == q
                assert key not in q.params

            # Remove multiple keys at a time (in this case all of them).
            q = furl.Query(items.original())
            if items.allitems():
                assert q.params
            allkeys = [key for key, value in items.allitems()]
            assert q.remove(allkeys) == q
            assert len(q.params) == 0

            # Remove the whole query string with True.
            q = furl.Query(items.original())
            if items.allitems():
                assert q.params
            assert q.remove(True) == q
            assert len(q.params) == 0

        # List of keys to remove.
        q = furl.Query([('a','1'), ('b', '2'), ('b', '3'), ('a', '4')])
        q.remove(['a', 'b'])
        assert not q.params.items()

        # List of items to remove.
        q = furl.Query([('a','1'), ('b', '2'), ('b', '3'), ('a', '4')])
        q.remove([('a', '1'), ('b', '3')])
        assert q.params.allitems() == [('b', '2'), ('a', '4')]

        # Dictionary of items to remove.
        q = furl.Query([('a','1'), ('b', '2'), ('b', '3'), ('a', '4')])
        q.remove({'b':'3', 'a':'1'})
        assert q.params.allitems() == [('b', '2'), ('a', '4')]

        # Multivalue dictionary of items to remove.
        q = furl.Query([('a','1'), ('b', '2'), ('b', '3'), ('a', '4')])
        omd = omdict1D([('a', '4'), ('b', '3'), ('b', '2')])
        q.remove(omd)
        assert q.params.allitems() == [('a', '1')]

    def test_params(self):
        # Basics.
        q = furl.Query('a=a&b=b')
        assert q.params == {'a': 'a', 'b': 'b'}
        q.params['sup'] = 'sup'
        assert q.params == {'a': 'a', 'b': 'b', 'sup': 'sup'}
        del q.params['a']
        assert q.params == {'b': 'b', 'sup': 'sup'}
        q.params['b'] = 'BLROP'
        assert q.params == {'b': 'BLROP', 'sup': 'sup'}

        # Blanks keys and values are kept.
        q = furl.Query('=')
        assert q.params == {'': ''} and str(q) == '='
        q = furl.Query('=&=')
        assert q.params.allitems() == [('', ''), ('', '')] and str(q) == '=&='
        q = furl.Query('a=&=b')
        assert q.params == {'a': '', '': 'b'} and str(q) == 'a=&=b'

        # ';' is a valid query delimeter.
        q = furl.Query('=;=')
        assert q.params.allitems() == [('', ''), ('', '')] and str(q) == '=&='
        q = furl.Query('a=a;b=b;c=')
        assert q.params == {
            'a': 'a', 'b': 'b', 'c': ''} and str(q) == 'a=a&b=b&c='

        # Non-string parameters are coerced to strings in the final
        # query string.
        q.params.clear()
        q.params[99] = 99
        q.params[None] = -1
        q.params['int'] = 1
        q.params['float'] = 0.39393
        assert str(q) == '99=99&None=-1&int=1&float=0.39393'

        # Spaces are encoded as '+'s. '+'s are encoded as '%2B'.
        q.params.clear()
        q.params['s s'] = 's s'
        q.params['p+p'] = 'p+p'
        assert str(q) == 's+s=s+s&p%2Bp=p%2Bp'

        # Params is an omdict (ordered multivalue dictionary).
        q.params.clear()
        q.params.add('1', '1').set('2', '4').add('1', '11').addlist(
            3, [3, 3, '3'])
        assert q.params.getlist('1') == ['1', '11'] and q.params['1'] == '1'
        assert q.params.getlist(3) == [3, 3, '3']

        # Assign various things to Query.params and make sure
        # Query.params is reinitialized, not replaced.
        for items in self.items:
            q.params = items.original()
            assert isinstance(q.params, omdict1D)

            pairs = izip(q.params.iterallitems(), items.iterallitems())
            for item1, item2 in pairs:
                assert item1 == item2

        # Value of '' -> '?param='. Value of None -> '?param'.
        q = furl.Query('slrp')
        assert str(q) == 'slrp' and q.params['slrp'] is None
        q = furl.Query('slrp=')
        assert str(q) == 'slrp=' and q.params['slrp'] == ''
        q = furl.Query('prp=&slrp')
        assert q.params['prp'] == '' and q.params['slrp'] is None
        q.params['slrp'] = ''
        assert str(q) == 'prp=&slrp=' and q.params['slrp'] == ''

    def _quote_items(self, items):
        # Calculate the expected querystring with proper query encoding.
        #   Valid query key characters: "/?:@-._~!$'()*,;"
        #   Valid query value characters: "/?:@-._~!$'()*,;="
        allitems_quoted = []
        for key, value in items.iterallitems():
            pair = (urllib.quote_plus(str(key), "/?:@-._~!$'()*,;"),
                    urllib.quote_plus(str(value), "/?:@-._~!$'()*,;="))
            allitems_quoted.append(pair)
        return allitems_quoted


class TestQueryCompositionInterface(unittest.TestCase):

    def test_interface(self):
        class tester(furl.QueryCompositionInterface):

            def __init__(self):
                furl.QueryCompositionInterface.__init__(self)

            def __setattr__(self, attr, value):
                fqci = furl.QueryCompositionInterface
                if not fqci.__setattr__(self, attr, value):
                    object.__setattr__(self, attr, value)

        t = tester()
        assert isinstance(t.query, furl.Query)
        assert str(t.query) == ''

        t.query = 'a=a&s=s s'
        assert isinstance(t.query, furl.Query)
        assert str(t.query) == 'a=a&s=s+s'
        assert t.args == t.query.params == {'a': 'a', 's': 's s'}


class TestFragment(unittest.TestCase):

    def test_basics(self):
        f = furl.Fragment()
        assert str(f.path) == '' and str(f.query) == '' and str(f) == ''

        f.args['sup'] = 'foo'
        assert str(f) == 'sup=foo'
        f.path = 'yasup'
        assert str(f) == 'yasup?sup=foo'
        f.path = '/yasup'
        assert str(f) == '/yasup?sup=foo'
        assert str(f.query) == 'sup=foo'
        f.query.params['sup'] = 'kwlpumps'
        assert str(f) == '/yasup?sup=kwlpumps'
        f.query = ''
        assert str(f) == '/yasup'
        f.path = ''
        assert str(f) == ''
        f.args['no'] = 'dads'
        f.query.params['hi'] = 'gr8job'
        assert str(f) == 'no=dads&hi=gr8job'

    def test_load(self):
        comps = [('', '', {}),
                 ('?', '%3F', {}),
                 ('??a??', '%3F%3Fa%3F%3F', {}),
                 ('??a??=', '', {'?a??': ''}),
                 ('schtoot', 'schtoot', {}),
                 ('sch/toot/YOEP', 'sch/toot/YOEP', {}),
                 ('/sch/toot/YOEP', '/sch/toot/YOEP', {}),
                 ('schtoot?', 'schtoot%3F', {}),
                 ('schtoot?NOP', 'schtoot%3FNOP', {}),
                 ('schtoot?NOP=', 'schtoot', {'NOP': ''}),
                 ('schtoot?=PARNT', 'schtoot', {'': 'PARNT'}),
                 ('schtoot?NOP=PARNT', 'schtoot', {'NOP': 'PARNT'}),
                 ('dog?machine?yes', 'dog%3Fmachine%3Fyes', {}),
                 ('dog?machine=?yes', 'dog', {'machine': '?yes'}),
                 ('schtoot?a=a&hok%20sprm', 'schtoot',
                  {'a': 'a', 'hok sprm': ''}),
                 ('schtoot?a=a&hok sprm', 'schtoot',
                  {'a': 'a', 'hok sprm': ''}),
                 ('sch/toot?a=a&hok sprm', 'sch/toot',
                  {'a': 'a', 'hok sprm': ''}),
                 ('/sch/toot?a=a&hok sprm', '/sch/toot',
                  {'a': 'a', 'hok sprm': ''}),
                 ]

        for fragment, path, query in comps:
            f = furl.Fragment()
            f.load(fragment)
            assert str(f.path) == path
            assert f.query.params == query

    def test_add(self):
        f = furl.Fragment('')
        assert f is f.add(path='one two three', args={'a': 'a', 's': 's s'})
        assert str(f) == 'one%20two%20three?a=a&s=s+s'

        f = furl.Fragment('break?legs=broken')
        assert f is f.add(path='horse bones', args={'a': 'a', 's': 's s'})
        assert str(f) == 'break/horse%20bones?legs=broken&a=a&s=s+s'

    def test_set(self):
        f = furl.Fragment('asdf?lol=sup&foo=blorp')
        assert f is f.set(path='one two three', args={'a': 'a', 's': 's s'})
        assert str(f) == 'one%20two%20three?a=a&s=s+s'

        assert f is f.set(path='!', separator=False)
        assert f.separator is False
        assert str(f) == '!a=a&s=s+s'

    def test_remove(self):
        f = furl.Fragment('a/path/great/job?lol=sup&foo=blorp')
        assert f is f.remove(path='job', args=['lol'])
        assert str(f) == 'a/path/great/?foo=blorp'

        assert f is f.remove(path=['path', 'great'], args=['foo'])
        assert str(f) == 'a/path/great/'
        assert f is f.remove(path=['path', 'great', ''])
        assert str(f) == 'a/'

        assert f is f.remove(fragment=True)
        assert str(f) == ''

    def test_encoding(self):
        f = furl.Fragment()
        f.path = "/?:@-._~!$&'()*+,;="
        assert str(f) == "/?:@-._~!$&'()*+,;="
        f.query = {'a': 'a', 'b b': 'NOPE'}
        assert str(f) == "/%3F:@-._~!$&'()*+,;=?a=a&b+b=NOPE"
        f.separator = False
        assert str(f) == "/?:@-._~!$&'()*+,;=a=a&b+b=NOPE"

        f = furl.Fragment()
        f.path = "/?:@-._~!$&'()*+,;= ^`<>[]"
        assert str(f) == "/?:@-._~!$&'()*+,;=%20%5E%60%3C%3E%5B%5D"
        f.query = {'a': 'a', 'b b': 'NOPE'}
        assert str(
            f) == "/%3F:@-._~!$&'()*+,;=%20%5E%60%3C%3E%5B%5D?a=a&b+b=NOPE"
        f.separator = False
        assert str(f) == "/?:@-._~!$&'()*+,;=%20%5E%60%3C%3E%5B%5Da=a&b+b=NOPE"

        f = furl.furl()
        f.fragment = 'a?b?c?d?'
        assert f.url == '#a?b?c?d?'
        # TODO(grun): Once encoding has been fixed with URLPath and
        # FragmentPath, the below line should be:
        #
        #  assert str(f.fragment) == str(f.path) == 'a?b?c?d?'
        #
        assert str(f.fragment) == 'a?b?c?d?'

    def test_nonzero(self):
        f = furl.Fragment()
        assert not f

        f = furl.Fragment('')
        assert not f

        f = furl.Fragment('asdf')
        assert f

        f = furl.Fragment()
        f.path = 'sup'
        assert f

        f = furl.Fragment()
        f.query = 'a=a'
        assert f

        f = furl.Fragment()
        f.path = 'sup'
        f.query = 'a=a'
        assert f

        f = furl.Fragment()
        f.path = 'sup'
        f.query = 'a=a'
        f.separator = False
        assert f


class TestFragmentCompositionInterface(unittest.TestCase):

    def test_interface(self):
        class tester(furl.FragmentCompositionInterface):

            def __init__(self):
                furl.FragmentCompositionInterface.__init__(self)

            def __setattr__(self, attr, value):
                ffci = furl.FragmentCompositionInterface
                if not ffci.__setattr__(self, attr, value):
                    object.__setattr__(self, attr, value)

        t = tester()
        assert isinstance(t.fragment, furl.Fragment)
        assert isinstance(t.fragment.path, furl.Path)
        assert isinstance(t.fragment.query, furl.Query)
        assert str(t.fragment) == ''
        assert t.fragment.separator
        assert str(t.fragment.path) == ''
        assert str(t.fragment.query) == ''

        t.fragment = 'animal meats'
        assert isinstance(t.fragment, furl.Fragment)
        t.fragment.path = 'pump/dump'
        t.fragment.query = 'a=a&s=s+s'
        assert isinstance(t.fragment.path, furl.Path)
        assert isinstance(t.fragment.query, furl.Query)
        assert str(t.fragment.path) == 'pump/dump'
        assert t.fragment.path.segments == ['pump', 'dump']
        assert not t.fragment.path.isabsolute
        assert str(t.fragment.query) == 'a=a&s=s+s'
        assert t.fragment.args == t.fragment.query.params == {
            'a': 'a', 's': 's s'}


class TestFurl(unittest.TestCase):

    def setUp(self):
        # Don't hide duplicate Warnings - test for all of them.
        warnings.simplefilter("always")

    def _param(self, url, key, val):
        # Note: urlparse.urlsplit() doesn't separate the query from the
        # path for all schemes, only those schemes in the list
        # urlparse.uses_query. So, as a result of using
        # urlparse.urlsplit(), this little helper function only works
        # when provided urls whos schemes are also in
        # urlparse.uses_query.
        items = urlparse.parse_qsl(urlparse.urlsplit(url).query, True)
        return (key, val) in items


    def test_unicode(self):
        url = u'http://ru.wikipedia.org/wiki/Восход_(ракета-носитель)'
        f = furl.furl(url)  # Accept a unicode URL without raising an exception.
        assert not isinstance(f.url, unicode)  # URLs cannot contain unicode.

    def test_scheme(self):
        assert furl.furl().scheme is None
        assert furl.furl('').scheme is None
        
        # Lowercase.
        assert furl.furl('/sup/').set(scheme='PrOtO').scheme == 'proto'
        
        # No scheme.
        for url in ['sup.txt', '/d/sup', '#flarg']:
            f = furl.furl(url)
            assert f.scheme is None and f.url == url
        
        # Protocol relative URLs.
        for url in ['//', '//sup.txt', '//arc.io/d/sup']:
            f = furl.furl(url)
            assert f.scheme == '' and f.url == url
        
        f = furl.furl('//sup.txt')
        assert f.scheme == ''
        f.scheme = None
        assert f.scheme is None and f.url == 'sup.txt'
        f.scheme = ''
        assert f.scheme == '' and f.url == '//sup.txt'

        # Schemes without slashes , like 'mailto:'.
        f = furl.furl('mailto:sup@sprp.ru')
        assert f.url == 'mailto:sup@sprp.ru'
        f = furl.furl('mailto://sup@sprp.ru')
        assert f.url == 'mailto:sup@sprp.ru'

        f = furl.furl('mailto:sproop:spraps@sprp.ru')
        assert f.scheme == 'mailto'
        assert f.username == 'sproop' and f.password == 'spraps'
        assert f.host == 'sprp.ru'

        f = furl.furl('mailto:')
        assert f.url == 'mailto:' and f.scheme == 'mailto'

    def test_username_and_password(self):
        # Empty usernames and passwords.
        for url in ['', 'http://www.pumps.com/']:
            f = furl.furl(url)
            assert f.username is None and f.password is None

        usernames = ['user', 'a-user_NAME$%^&09']
        passwords = ['pass', 'a-PASS_word$%^&09']
        baseurl = 'http://www.google.com/'

        # Username only.
        userurl = 'http://%s@www.google.com/'
        for username in usernames:
            f = furl.furl(userurl % username)
            assert f.username == username and f.password is None

            f = furl.furl(baseurl)
            f.username = username
            assert f.username == username and f.password is None
            assert f.url == userurl % username

            f = furl.furl(baseurl)
            f.set(username=username)
            assert f.username == username and f.password is None
            assert f.url == userurl % username

            f.remove(username=True)
            assert f.username is None and f.password is None
            assert f.url == baseurl

        # Password only.
        passurl = 'http://:%s@www.google.com/'
        for password in passwords:
            f = furl.furl(passurl % password)
            assert f.password == password and f.username is None

            f = furl.furl(baseurl)
            f.password = password
            assert f.password == password and f.username is None
            assert f.url == passurl % password

            f = furl.furl(baseurl)
            f.set(password=password)
            assert f.password == password and f.username is None
            assert f.url == passurl % password

            f.remove(password=True)
            assert not f.username and not f.password
            assert f.url == baseurl

        # Username and password.
        userpassurl = 'http://%s:%s@www.google.com/'
        for username in usernames:
            for password in passwords:
                f = furl.furl(userpassurl % (username, password))
                assert f.username == username and f.password == password

                f = furl.furl(baseurl)
                f.username = username
                f.password = password
                assert f.username == username and f.password == password
                assert f.url == userpassurl % (username, password)

                f = furl.furl(baseurl)
                f.set(username=username, password=password)
                assert f.username == username and f.password == password
                assert f.url == userpassurl % (username, password)

                f = furl.furl(baseurl)
                f.remove(username=True, password=True)
                assert not f.username and not f.password
                assert f.url == baseurl

        # Username and password in the network location string.
        f = furl.furl()
        f.netloc = 'user@domain.com'
        assert f.username == 'user' and not f.password
        assert f.netloc == 'user@domain.com'

        f = furl.furl()
        f.netloc = ':pass@domain.com'
        assert not f.username and f.password == 'pass'
        assert f.netloc == ':pass@domain.com'

        f = furl.furl()
        f.netloc = 'user:pass@domain.com'
        assert f.username == 'user' and f.password == 'pass'
        assert f.netloc == 'user:pass@domain.com'
        f = furl.furl()
        assert f.username is f.password is None
        f.username = 'uu'
        assert f.username == 'uu' and f.password is None and f.url == 'uu@'
        f.password = 'pp'
        assert f.username == 'uu' and f.password == 'pp' and f.url == 'uu:pp@'
        f.username = ''
        assert f.username == '' and f.password == 'pp' and f.url == ':pp@'
        f.password = ''
        assert f.username == f.password == '' and f.url == ':@'
        f.password = None
        assert f.username == '' and f.password is None and f.url == '@'
        f.username = None
        assert f.username is f.password is None and f.url == ''
        f.password = ''
        assert f.username is None and f.password == '' and f.url == ':@'

    def test_basics(self):
        url = 'hTtP://www.pumps.com/'
        f = furl.furl(url)
        assert f.scheme == 'http'
        assert f.netloc == 'www.pumps.com'
        assert f.host == 'www.pumps.com'
        assert f.port == 80
        assert str(f.path) == '/'
        assert str(f.query) == ''
        assert f.args == f.query.params == {}
        assert str(f.fragment) == ''
        assert f.url == str(f) == url.lower()
        assert f.url == furl.furl(f).url == furl.furl(f.url).url
        assert f is not f.copy() and f.url == f.copy().url

        url = 'HTTPS://wWw.YAHOO.cO.UK/one/two/three?a=a&b=b&m=m%26m#fragment'
        f = furl.furl(url)
        assert f.scheme == 'https'
        assert f.netloc == 'www.yahoo.co.uk'
        assert f.host == 'www.yahoo.co.uk'
        assert f.port == 443
        assert str(f.path) == '/one/two/three'
        assert str(f.query) == 'a=a&b=b&m=m%26m'
        assert f.args == f.query.params == {'a': 'a', 'b': 'b', 'm': 'm&m'}
        assert str(f.fragment) == 'fragment'
        assert f.url == str(f) == url.lower()
        assert f.url == furl.furl(f).url == furl.furl(f.url).url
        assert f is not f.copy() and f.url == f.copy().url

        url = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl%20string#frag'
        f = furl.furl(url)
        assert f.scheme == 'sup'
        assert f.netloc == '192.168.1.102:8080'
        assert f.host == '192.168.1.102'
        assert f.port == 8080
        assert str(f.path) == '///one//a%20b////'
        assert str(f.query) == 's=kwl+string'
        assert f.args == f.query.params == {'s': 'kwl string'}
        assert str(f.fragment) == 'frag'
        quoted = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl+string#frag'
        assert f.url == str(f) == quoted
        assert f.url == furl.furl(f).url == furl.furl(f.url).url
        assert f is not f.copy() and f.url == f.copy().url

        # URL paths are optionally absolute if scheme and netloc are
        # empty.
        f = furl.furl()
        f.path.segments = ['pumps']
        assert str(f.path) == 'pumps'
        f.path = 'pumps'
        assert str(f.path) == 'pumps'

        # Fragment paths are optionally absolute, and not absolute by
        # default.
        f = furl.furl()
        f.fragment.path.segments = ['pumps']
        assert str(f.fragment.path) == 'pumps'
        f.fragment.path = 'pumps'
        assert str(f.fragment.path) == 'pumps'

        # URLs comprised of a netloc string only should not be prefixed
        # with '//', as-is the default behavior of
        # urlparse.urlunsplit().
        f = furl.furl()
        assert f.set(host='foo').url == 'foo'
        assert f.set(host='pumps.com').url == 'pumps.com'
        assert f.set(host='pumps.com', port=88).url == 'pumps.com:88'
        assert f.set(netloc='pumps.com:88').url == 'pumps.com:88'

    def test_basic_manipulation(self):
        f = furl.furl('http://www.pumps.com/')

        f.args.setdefault('foo', 'blah')
        assert str(f) == 'http://www.pumps.com/?foo=blah'
        f.query.params['foo'] = 'eep'
        assert str(f) == 'http://www.pumps.com/?foo=eep'

        f.port = 99
        assert str(f) == 'http://www.pumps.com:99/?foo=eep'

        f.netloc = 'www.yahoo.com:220'
        assert str(f) == 'http://www.yahoo.com:220/?foo=eep'

        f.netloc = 'www.yahoo.com'
        assert f.port == 80
        assert str(f) == 'http://www.yahoo.com/?foo=eep'

        f.scheme = 'sup'
        assert str(f) == 'sup://www.yahoo.com:80/?foo=eep'

        f.port = None
        assert str(f) == 'sup://www.yahoo.com/?foo=eep'

        f.fragment = 'sup'
        assert str(f) == 'sup://www.yahoo.com/?foo=eep#sup'

        f.path = 'hay supppp'
        assert str(f) == 'sup://www.yahoo.com/hay%20supppp?foo=eep#sup'

        f.args['space'] = '1 2'
        assert str(
            f) == 'sup://www.yahoo.com/hay%20supppp?foo=eep&space=1+2#sup'

        del f.args['foo']
        assert str(f) == 'sup://www.yahoo.com/hay%20supppp?space=1+2#sup'

        f.host = 'ohay.com'
        assert str(f) == 'sup://ohay.com/hay%20supppp?space=1+2#sup'

    def test_odd_urls(self):
        # Empty.
        f = furl.furl('')
        assert f.username is f.password is None
        assert f.scheme is f.host is f.port is f.netloc is None
        assert str(f.path) == ''
        assert str(f.query) == ''
        assert f.args == f.query.params == {}
        assert str(f.fragment) == ''
        assert f.url == ''

        # Keep in mind that ';' is a query delimeter for both the URL
        # query and the fragment query, resulting in the str(path),
        # str(query), and str(fragment) values below.
        url = (
            "sup://example.com/:@-._~!$&'()*+,=;:@-._~!$&'()*+,=:@-._~!$&'()*+"
            ",==?/?:@-._~!$'()*+,;=/?:@-._~!$'()*+,;==#/?:@-._~!$&'()*+,;=")
        pathstr = "/:@-._~!$&'()*+,=;:@-._~!$&'()*+,=:@-._~!$&'()*+,=="
        querystr = "/?:@-._~!$'()*+,=&=/?:@-._~!$'()*+,&=="
        fragmentstr = "/?:@-._~!$=&'()*+,=&="
        f = furl.furl(url)
        assert f.scheme == 'sup'
        assert f.host == 'example.com'
        assert f.port is None
        assert f.netloc == 'example.com'
        assert str(f.path) == pathstr
        assert str(f.query) == querystr
        assert str(f.fragment) == fragmentstr

        # Scheme only.
        f = furl.furl('sup://')
        assert f.scheme == 'sup'
        assert f.host is f.port is f.netloc is None
        assert str(f.path) == ''
        assert str(f.query) == ''
        assert f.args == f.query.params == {}
        assert str(f.fragment) == ''
        assert f.url == 'sup://' and f.netloc is None
        f.scheme = None
        assert f.scheme is None and f.netloc is None and f.url == ''
        f.scheme = ''
        assert f.scheme == '' and f.netloc is None and f.url == '//'

        # Host only.
        f = furl.furl().set(host='pumps.meat')
        assert f.url == 'pumps.meat' and f.netloc == f.host == 'pumps.meat'
        f.host = None
        assert f.url == '' and f.host is f.netloc is None
        f.host = ''
        assert f.url == '' and f.host == f.netloc == ''

        # Port only.
        f = furl.furl()
        f.port = 99
        assert f.url == ':99' and f.netloc is not None
        f.port = None
        assert f.url == '' and f.netloc is None

        # urlparse.urlsplit() treats the first two '//' as the beginning
        # of a netloc, even if the netloc is empty.
        f = furl.furl('////path')
        assert f.url == '//path' and str(f.path) == '//path'

        # TODO(grun): Test more odd urls.

    def test_hosts(self):
        # No host.
        url = 'http:///index.html'
        f = furl.furl(url)
        assert f.host is None and furl.furl(url).url == url

        # Valid IPv4 and IPv6 addresses.
        f = furl.furl('http://192.168.1.101')
        f = furl.furl('http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/')

        # Invalid IPv4 addresses shouldn't raise an exception because
        # urlparse.urlsplit() doesn't raise an exception on invalid IPv4
        # addresses.
        f = furl.furl('http://1.2.3.4.5.6/')

        # Invalid, but well-formed, IPv6 addresses shouldn't raise an
        # exception because urlparse.urlsplit() doesn't raise an
        # exception on invalid IPv6 addresses.
        furl.furl('http://[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]/')

        # Malformed IPv6 should raise an exception because
        # urlparse.urlsplit() raises an exception in Python v2.7+. In
        # Python <= 2.6, urlsplit() doesn't raise a ValueError on
        # malformed IPv6 addresses.
        if PYTHON_27PLUS:
            with self.assertRaises(ValueError):
                furl.furl('http://[0:0:0:0:0:0:0:1/')
            with self.assertRaises(ValueError):
                furl.furl('http://0:0:0:0:0:0:0:1]/')

    def test_netlocs(self):
        f = furl.furl('http://pumps.com/')
        netloc = '1.2.3.4.5.6:999'
        f.netloc = netloc
        assert f.netloc == netloc
        assert f.host == '1.2.3.4.5.6'
        assert f.port == 999

        netloc = '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]:888'
        f.netloc = netloc
        assert f.netloc == netloc
        assert f.host == '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]'
        assert f.port == 888

        # Malformed IPv6 should raise an exception because
        # urlparse.urlsplit() raises an exception in Python v2.7+.
        if PYTHON_27PLUS:
            with self.assertRaises(ValueError):
                f.netloc = '[0:0:0:0:0:0:0:1'
            with self.assertRaises(ValueError):
                f.netloc = '0:0:0:0:0:0:0:1]'

        # Invalid ports.
        with self.assertRaises(ValueError):
            f.netloc = '[0:0:0:0:0:0:0:1]:alksdflasdfasdf'
        with self.assertRaises(ValueError):
            f.netloc = 'pump2pump.org:777777777777'

        # No side effects.
        assert f.host == '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]'
        assert f.port == 888

    def test_ports(self):
        # Default port values.
        assert furl.furl('http://www.pumps.com/').port == 80
        assert furl.furl('https://www.pumps.com/').port == 443
        assert furl.furl('undefined://www.pumps.com/').port is None

        # Override default port values.
        assert furl.furl('http://www.pumps.com:9000/').port == 9000
        assert furl.furl('https://www.pumps.com:9000/').port == 9000
        assert furl.furl('undefined://www.pumps.com:9000/').port == 9000

        # Reset the port.
        f = furl.furl('http://www.pumps.com:9000/')
        f.port = None
        assert f.url == 'http://www.pumps.com/'
        assert f.port == 80

        f = furl.furl('undefined://www.pumps.com:9000/')
        f.port = None
        assert f.url == 'undefined://www.pumps.com/'
        assert f.port is None

        # Invalid port raises ValueError with no side effects.
        with self.assertRaises(ValueError):
            furl.furl('http://www.pumps.com:invalid/')

        url = 'http://www.pumps.com:400/'
        f = furl.furl(url)
        assert f.port == 400
        with self.assertRaises(ValueError):
            f.port = 'asdf'
        assert f.url == url
        f.port = 9999
        with self.assertRaises(ValueError):
            f.port = []
        with self.assertRaises(ValueError):
            f.port = -1
        with self.assertRaises(ValueError):
            f.port = 77777777777
        assert f.port == 9999
        assert f.url == 'http://www.pumps.com:9999/'

        self.assertRaises(f.set, port='asdf')

    def test_add(self):
        f = furl.furl('http://pumps.com/')

        assert f is f.add(args={'a': 'a', 'm': 'm&m'}, path='kwl jump',
                          fragment_path='1', fragment_args={'f': 'frp'})
        assert self._param(f.url, 'a', 'a')
        assert self._param(f.url, 'm', 'm&m')
        assert str(f.fragment) == '1?f=frp'
        assert str(f.path) == urlparse.urlsplit(f.url).path == '/kwl%20jump'

        assert f is f.add(path='dir', fragment_path='23', args={'b': 'b'},
                          fragment_args={'b': 'bewp'})
        assert self._param(f.url, 'a', 'a')
        assert self._param(f.url, 'm', 'm&m')
        assert self._param(f.url, 'b', 'b')
        assert str(f.path) == '/kwl%20jump/dir'
        assert str(f.fragment) == '1/23?f=frp&b=bewp'

        # Supplying both <args> and <query_params> should raise a
        # warning.
        with warnings.catch_warnings(True) as w1:
            f.add(args={'a': '1'}, query_params={'a': '2'})
            assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
            assert self._param(
                f.url, 'a', '1') and self._param(f.url, 'a', '2')
            params = f.args.allitems()
            assert params.index(('a', '1')) < params.index(('a', '2'))

    def test_set(self):
        f = furl.furl('http://pumps.com/kwl%20jump/dir')
        assert f is f.set(args={'no': 'nope'}, fragment='sup')
        assert 'a' not in f.args
        assert 'b' not in f.args
        assert f.url == 'http://pumps.com/kwl%20jump/dir?no=nope#sup'

        # No conflict warnings between <host>/<port> and <netloc>, or
        # <query> and <params>.
        assert f is f.set(args={'a': 'a a'}, path='path path/dir', port='999',
                          fragment='moresup', scheme='sup', host='host')
        assert str(f.path) == '/path%20path/dir'
        assert f.url == 'sup://host:999/path%20path/dir?a=a+a#moresup'

        # Path as a list of path segments to join.
        assert f is f.set(path=['d1', 'd2'])
        assert f.url == 'sup://host:999/d1/d2?a=a+a#moresup'
        assert f is f.add(path=['/d3/', '/d4/'])
        assert f.url == 'sup://host:999/d1/d2/%2Fd3%2F/%2Fd4%2F?a=a+a#moresup'

        # Set a lot of stuff (but avoid conflicts, which are tested
        # below).
        f.set(
            query_params={'k': 'k'}, fragment_path='no scrubs', scheme='morp',
            host='myhouse', port=69, path='j$j*m#n', fragment_args={'f': 'f'})
        assert f.url == 'morp://myhouse:69/j$j*m%23n?k=k#no%20scrubs?f=f'

        # No side effects.
        oldurl = f.url
        with self.assertRaises(ValueError):
            f.set(args={'a': 'a a'}, path='path path/dir', port='INVALID_PORT',
                  fragment='moresup', scheme='sup', host='host')
        assert f.url == oldurl
        with warnings.catch_warnings(True) as w1:
            self.assertRaises(
                ValueError, f.set, netloc='nope.com:99', port='NOPE')
            assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
        assert f.url == oldurl

        # Separator isn't reset with set().
        f = furl.Fragment()
        f.separator = False
        f.set(path='flush', args={'dad': 'nope'})
        assert str(f) == 'flushdad=nope'

        # Test warnings for potentially overlapping parameters.
        f = furl.furl('http://pumps.com')
        warnings.simplefilter("always")

        # Host, port, and netloc overlap - host and port take
        # precedence.
        with warnings.catch_warnings(True) as w1:
            f.set(netloc='dumps.com:99', host='ohay.com')
            assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
            f.host == 'ohay.com'
            f.port == 99
        with warnings.catch_warnings(True) as w2:
            f.set(netloc='dumps.com:99', port=88)
            assert len(w2) == 1 and issubclass(w2[0].category, UserWarning)
            f.port == 88
        with warnings.catch_warnings(True) as w3:
            f.set(netloc='dumps.com:99', host='ohay.com', port=88)
            assert len(w3) == 1 and issubclass(w3[0].category, UserWarning)

        # Query, args, and query_params overlap - args and query_params
        # take precedence.
        with warnings.catch_warnings(True) as w4:
            f.set(query='yosup', args={'a': 'a', 'b': 'b'})
            assert len(w4) == 1 and issubclass(w4[0].category, UserWarning)
            assert self._param(f.url, 'a', 'a')
            assert self._param(f.url, 'b', 'b')
        with warnings.catch_warnings(True) as w5:
            f.set(query='yosup', query_params={'a': 'a', 'b': 'b'})
            assert len(w5) == 1 and issubclass(w5[0].category, UserWarning)
            assert self._param(f.url, 'a', 'a')
            assert self._param(f.url, 'b', 'b')
        with warnings.catch_warnings(True) as w6:
            f.set(args={'a': 'a', 'b': 'b'}, query_params={'c': 'c', 'd': 'd'})
            assert len(w6) == 1 and issubclass(w6[0].category, UserWarning)
            assert self._param(f.url, 'c', 'c')
            assert self._param(f.url, 'd', 'd')

        # Fragment, fragment_path, fragment_args, and fragment_separator
        # overlap - fragment_separator, fragment_path, and fragment_args
        # take precedence.
        with warnings.catch_warnings(True) as w7:
            f.set(fragment='hi', fragment_path='!', fragment_args={'a': 'a'},
                  fragment_separator=False)
            assert len(w7) == 1 and issubclass(w7[0].category, UserWarning)
            assert str(f.fragment) == '!a=a'
        with warnings.catch_warnings(True) as w8:
            f.set(fragment='hi', fragment_path='bye')
            assert len(w8) == 1 and issubclass(w8[0].category, UserWarning)
            assert str(f.fragment) == 'bye'
        with warnings.catch_warnings(True) as w9:
            f.set(fragment='hi', fragment_args={'a': 'a'})
            assert len(w9) == 1 and issubclass(w9[0].category, UserWarning)
            assert str(f.fragment) == 'hia=a'
        with warnings.catch_warnings(True) as w10:
            f.set(fragment='!?a=a', fragment_separator=False)
            assert len(w10) == 1 and issubclass(w10[0].category, UserWarning)
            assert str(f.fragment) == '!a=a'

    def test_remove(self):
        url = ('http://u:p@host:69/a/big/path/?a=a&b=b&s=s+s#a frag?with=args'
               '&a=a')
        f = furl.furl(url)

        # Remove without parameters removes nothing.
        assert f.url == f.remove().url

        # username, password, and port must be True.
        assert f == f.copy().remove(
            username='nope', password='nope', port='nope')

        # Basics.
        assert f is f.remove(fragment=True, args=['a', 'b'], path='path/',
                             username=True, password=True, port=True)
        assert f.url == 'http://host/a/big/?s=s+s'

        # No errors are thrown when removing URL components that don't exist.
        f = furl.furl(url)
        assert f is f.remove(fragment_path=['asdf'], fragment_args=['asdf'],
                             args=['asdf'], path=['ppp', 'ump'])
        assert self._param(f.url, 'a', 'a')
        assert self._param(f.url, 'b', 'b')
        assert self._param(f.url, 's', 's s')
        assert str(f.path) == '/a/big/path/'
        assert str(f.fragment.path) == 'a%20frag'
        assert f.fragment.args == {'a': 'a', 'with': 'args'}

        # Path as a list of paths to join before removing.
        assert f is f.remove(fragment_path='a frag', fragment_args=['a'],
                             query_params=['a', 'b'], path=['big', 'path', ''],
                             port=True)
        assert f.url == 'http://u:p@host/a/?s=s+s#with=args'

        assert f is f.remove(
            path=True, query=True, fragment=True, username=True,
            password=True)
        assert f.url == 'http://host'

    def test_join(self):
        empty_tests = ['', '/meat', '/meat/pump?a=a&b=b#fragsup',
                       'sup://www.pumps.org/brg/pap/mrf?a=b&c=d#frag?sup', ]
        run_tests = [
            # Join full urls.
            ('unknown://www.yahoo.com', 'unknown://www.yahoo.com'),
            ('unknown://www.yahoo.com?one=two&three=four',
             'unknown://www.yahoo.com?one=two&three=four'),
            ('unknown://www.yahoo.com/new/url/?one=two#blrp',
             'unknown://www.yahoo.com/new/url/?one=two#blrp'),

            # Absolute paths ('/foo').
            ('/pump', 'unknown://www.yahoo.com/pump'),
            ('/pump/2/dump', 'unknown://www.yahoo.com/pump/2/dump'),
            ('/pump/2/dump/', 'unknown://www.yahoo.com/pump/2/dump/'),

            # Relative paths ('../foo').
            ('./crit/', 'unknown://www.yahoo.com/pump/2/dump/crit/'),
            ('.././../././././srp', 'unknown://www.yahoo.com/pump/2/srp'),
            ('../././../nop', 'unknown://www.yahoo.com/nop'),

            # Query included.
            ('/erp/?one=two', 'unknown://www.yahoo.com/erp/?one=two'),
            ('morp?three=four', 'unknown://www.yahoo.com/erp/morp?three=four'),
            ('/root/pumps?five=six',
             'unknown://www.yahoo.com/root/pumps?five=six'),

            # Fragment included.
            ('#sup', 'unknown://www.yahoo.com/root/pumps?five=six#sup'),
            ('/reset?one=two#yepYEP',
             'unknown://www.yahoo.com/reset?one=two#yepYEP'),
            ('./slurm#uwantpump?', 'unknown://www.yahoo.com/slurm#uwantpump?')
        ]

        for test in empty_tests:
            f = furl.furl().join(test)
            assert f.url == test

        f = furl.furl('')
        for join, result in run_tests:
            assert f is f.join(join) and f.url == result

        # Join other furl object, which serialize to strings with str().
        f = furl.furl('')
        for join, result in run_tests:
            tojoin = furl.furl(join)
            assert f is f.join(tojoin) and f.url == result

    def test_equality(self):
        assert furl.furl() is not furl.furl() and furl.furl() == furl.furl()

        url = 'https://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
        assert furl.furl(url) == furl.furl(url)
        assert furl.furl(url).remove(path=True) != furl.furl(url)

    def test_urlsplit(self):
        # Without any delimeters like '://' or '/', the input should be
        # treated as a path.
        urls = ['sup', '127.0.0.1', 'www.google.com', '192.168.1.1:8000']
        for url in urls:
            assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
            assert furl.urlsplit(url).path == urlparse.urlsplit(url).path

        # No changes to existing urlsplit() behavior for known schemes.
        url = 'http://www.pumps.com/'
        assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
        assert furl.urlsplit(url) == urlparse.urlsplit(url)

        url = 'https://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
        assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
        assert furl.urlsplit(url) == urlparse.urlsplit(url)

        # Properly split the query from the path for unknown schemes.
        url = 'unknown://www.yahoo.com?one=two&three=four'
        correct = ('unknown', 'www.yahoo.com', '', 'one=two&three=four', '')
        assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
        assert furl.urlsplit(url) == correct

        url = 'sup://192.168.1.102:8080///one//two////?s=kwl%20string#frag'
        correct = ('sup', '192.168.1.102:8080', '///one//two////',
                   's=kwl%20string', 'frag')
        assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
        assert furl.urlsplit(url) == correct

        url = 'crazyyy://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#frag'
        correct = ('crazyyy', 'www.yahoo.co.uk', '/one/two/three',
                   'a=a&b=b&m=m%26m', 'frag')
        assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
        assert furl.urlsplit(url) == correct

    def test_join_path_segments(self):
        jps = furl.join_path_segments

        # Empty.
        assert jps() == []
        assert jps([]) == []
        assert jps([], [], [], []) == []

        # Null strings.
        #   [''] means nothing, or an empty string, in the final path
        #     segments.
        #   ['', ''] is preserved as a slash in the final path segments.
        assert jps(['']) == []
        assert jps([''], ['']) == []
        assert jps([''], [''], ['']) == []
        assert jps([''], ['', '']) == ['', '']
        assert jps([''], [''], [''], ['']) == []
        assert jps(['', ''], ['', '']) == ['', '', '']
        assert jps(['', '', ''], ['', '']) == ['', '', '', '']
        assert jps(['', '', '', '', '', '']) == ['', '', '', '', '', '']
        assert jps(['', '', '', ''], ['', '']) == ['', '', '', '', '']
        assert jps(['', '', '', ''], ['', ''], ['']) == ['', '', '', '', '']
        assert jps(['', '', '', ''], ['', '', '']) == ['', '', '', '', '', '']

        # Basics.
        assert jps(['a']) == ['a']
        assert jps(['a', 'b']) == ['a', 'b']
        assert jps(['a'], ['b']) == ['a', 'b']
        assert jps(['1', '2', '3'], ['4', '5']) == ['1', '2', '3', '4', '5']

        # A trailing slash is preserved if no new slash is being added.
        #   ex: ['a', ''] + ['b'] == ['a', 'b'], or 'a/' + 'b' == 'a/b'
        assert jps(['a', ''], ['b']) == ['a', 'b']
        assert jps(['a'], [''], ['b']) == ['a', 'b']
        assert jps(['', 'a', ''], ['b']) == ['', 'a', 'b']
        assert jps(['', 'a', ''], ['b', '']) == ['', 'a', 'b', '']

        # A new slash is preserved if no trailing slash exists.
        #   ex: ['a'] + ['', 'b'] == ['a', 'b'], or 'a' + '/b' == 'a/b'
        assert jps(['a'], ['', 'b']) == ['a', 'b']
        assert jps(['a'], [''], ['b']) == ['a', 'b']
        assert jps(['', 'a'], ['', 'b']) == ['', 'a', 'b']
        assert jps(['', 'a', ''], ['b', '']) == ['', 'a', 'b', '']
        assert jps(['', 'a', ''], ['b'], ['']) == ['', 'a', 'b']
        assert jps(['', 'a', ''], ['b'], ['', '']) == ['', 'a', 'b', '']

        # A trailing slash and a new slash means that an extra slash
        # will exist afterwords.
        # ex: ['a', ''] + ['', 'b'] == ['a', '', 'b'], or 'a/' + '/b'
        #   == 'a//b'
        assert jps(['a', ''], ['', 'b']) == ['a', '', 'b']
        assert jps(['a'], [''], [''], ['b']) == ['a', 'b']
        assert jps(['', 'a', ''], ['', 'b']) == ['', 'a', '', 'b']
        assert jps(['', 'a'], [''], ['b', '']) == ['', 'a', 'b', '']
        assert jps(['', 'a'], [''], [''], ['b'], ['']) == ['', 'a', 'b']
        assert jps(['', 'a'], [''], [''], ['b'], ['', '']) == [
            '', 'a', 'b', '']
        assert jps(['', 'a'], ['', ''], ['b'], ['', '']) == ['', 'a', 'b', '']
        assert jps(['', 'a'], ['', '', ''], ['b']) == ['', 'a', '', 'b']
        assert jps(['', 'a', ''], ['', '', ''], ['', 'b']) == [
            '', 'a', '', '', '', 'b']
        assert jps(['a', '', ''], ['', '', ''], ['', 'b']) == [
            'a', '', '', '', '', 'b']

        # Path segments blocks without slashes, are combined as
        # expected.
        assert jps(['a', 'b'], ['c', 'd']) == ['a', 'b', 'c', 'd']
        assert jps(['a'], ['b'], ['c'], ['d']) == ['a', 'b', 'c', 'd']
        assert jps(['a', 'b', 'c', 'd'], ['e']) == ['a', 'b', 'c', 'd', 'e']
        assert jps(['a', 'b', 'c'], ['d'], ['e', 'f']) == [
            'a', 'b', 'c', 'd', 'e', 'f']

        # Putting it all together.
        assert jps(['a', '', 'b'], ['', 'c', 'd']) == ['a', '', 'b', 'c', 'd']
        assert jps(['a', '', 'b', ''], ['c', 'd']) == ['a', '', 'b', 'c', 'd']
        assert jps(['a', '', 'b', ''], ['c', 'd'], ['', 'e']) == [
            'a', '', 'b', 'c', 'd', 'e']
        assert jps(['', 'a', '', 'b', ''], ['', 'c']) == [
            '', 'a', '', 'b', '', 'c']
        assert jps(['', 'a', ''], ['', 'b', ''], ['', 'c']) == [
            '', 'a', '', 'b', '', 'c']

    def test_remove_path_segments(self):
        rps = furl.remove_path_segments

        # [''] represents a slash, equivalent to ['',''].

        # Basics.
        assert rps([], []) == []
        assert rps([''], ['']) == []
        assert rps(['a'], ['a']) == []
        assert rps(['a'], ['', 'a']) == ['a']
        assert rps(['a'], ['a', '']) == ['a']
        assert rps(['a'], ['', 'a', '']) == ['a']

        # Slash manipulation.
        assert rps([''], ['', '']) == []
        assert rps(['', ''], ['']) == []
        assert rps(['', ''], ['', '']) == []
        assert rps(['', 'a', 'b', 'c'], ['b', 'c']) == ['', 'a', '']
        assert rps(['', 'a', 'b', 'c'], ['', 'b', 'c']) == ['', 'a']
        assert rps(['', 'a', '', ''], ['']) == ['', 'a', '']
        assert rps(['', 'a', '', ''], ['', '']) == ['', 'a', '']
        assert rps(['', 'a', '', ''], ['', '', '']) == ['', 'a']

        # Remove a portion of the path from the tail of the original
        # path.
        assert rps(['', 'a', 'b', ''], ['', 'a', 'b', '']) == []
        assert rps(['', 'a', 'b', ''], ['a', 'b', '']) == ['', '']
        assert rps(['', 'a', 'b', ''], ['b', '']) == ['', 'a', '']
        assert rps(['', 'a', 'b', ''], ['', 'b', '']) == ['', 'a']
        assert rps(['', 'a', 'b', ''], ['', '']) == ['', 'a', 'b']
        assert rps(['', 'a', 'b', ''], ['']) == ['', 'a', 'b']
        assert rps(['', 'a', 'b', ''], []) == ['', 'a', 'b', '']

        assert rps(['', 'a', 'b', 'c'], ['', 'a', 'b', 'c']) == []
        assert rps(['', 'a', 'b', 'c'], ['a', 'b', 'c']) == ['', '']
        assert rps(['', 'a', 'b', 'c'], ['b', 'c']) == ['', 'a', '']
        assert rps(['', 'a', 'b', 'c'], ['', 'b', 'c']) == ['', 'a']
        assert rps(['', 'a', 'b', 'c'], ['c']) == ['', 'a', 'b', '']
        assert rps(['', 'a', 'b', 'c'], ['', 'c']) == ['', 'a', 'b']
        assert rps(['', 'a', 'b', 'c'], []) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['']) == ['', 'a', 'b', 'c']

        # Attempt to remove valid subsections, but subsections not from
        # the end of the original path.
        assert rps(['', 'a', 'b', 'c'], ['', 'a', 'b', '']) == [
            '', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a', 'b']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['a', 'b']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['a', 'b', '']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a', 'b']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a', 'b', '']) == [
            '', 'a', 'b', 'c']

        assert rps(['', 'a', 'b', 'c'], ['a']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['a', '']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a', '']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', 'a', '', '']) == [
            '', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', '', 'a', '', '']) == [
            '', 'a', 'b', 'c']

        assert rps(['', 'a', 'b', 'c'], ['']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['', '']) == ['', 'a', 'b', 'c']
        assert rps(['', 'a', 'b', 'c'], ['c', '']) == ['', 'a', 'b', 'c']

        # Attempt to remove segments longer than the original.
        assert rps([], ['a']) == []
        assert rps([], ['a', 'b']) == []
        assert rps(['a'], ['a', 'b']) == ['a']
        assert rps(['a', 'a'], ['a', 'a', 'a']) == ['a', 'a']

    def test_is_valid_port(self):
        valids = [1, 2, 3, 65535, 119, 2930]
        invalids = [-1, -9999, 0, 'a', [], (0), {1: 1}, 65536, 99999, {}, None]

        for port in valids:
            assert furl.is_valid_port(port)
        for port in invalids:
            assert not furl.is_valid_port(port)

    def test_is_valid_encoded_path_segment(segment):
        valids = [('abcdefghijklmnopqrstuvwxyz'
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                   '0123456789' '-._~' ":@!$&'()*+,;="),
                  '', 'a', 'asdf', 'a%20a', '%3F', ]
        invalids = [' ^`<>[]"#/?', ' ', '%3Z', '/', '?']

        for valid in valids:
            assert furl.is_valid_encoded_path_segment(valid)
        for invalid in invalids:
            assert not furl.is_valid_encoded_path_segment(invalid)

    def test_is_valid_encoded_query_key(key):
        valids = [('abcdefghijklmnopqrstuvwxyz'
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                   '0123456789' '-._~' ":@!$&'()*+,;" '/?'),
                  '', 'a', 'asdf', 'a%20a', '%3F', 'a+a', '/', '?', ]
        invalids = [' ^`<>[]"#', ' ', '%3Z', '#']

        for valid in valids:
            assert furl.is_valid_encoded_query_key(valid)
        for invalid in invalids:
            assert not furl.is_valid_encoded_query_key(invalid)

    def test_is_valid_encoded_query_value(value):
        valids = [('abcdefghijklmnopqrstuvwxyz'
                   'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                   '0123456789' '-._~' ":@!$&'()*+,;" '/?='),
                  '', 'a', 'asdf', 'a%20a', '%3F', 'a+a', '/', '?', '=']
        invalids = [' ^`<>[]"#', ' ', '%3Z', '#']

        for valid in valids:
            assert furl.is_valid_encoded_query_value(valid)
        for invalid in invalids:
            assert not furl.is_valid_encoded_query_value(invalid)
