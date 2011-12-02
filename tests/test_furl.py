#
# furl: URL manipulation made simple.
#
# Arthur Grunseid
# grunseid.com
# grunseid@gmail.com
#
# Copyright: LOLOLOL
#
# License: Build Amazing Things

import urllib
import unittest
import urlparse
import warnings

import furl

class TestPath(unittest.TestCase):
  def test_isdir_isfile(self):
    for path in ['', '/']:
      p = furl.Path(path)
      assert p.isdir
      assert not p.isfile
    
    for path in ['dir1/', 'd1/d2/', 'd/d/d/d/d/', '/', '/dir1/', '/d1/d2/d3/']:
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
    encoded = ['a%20a', '/%7haypepps/']
    unencoded = ['a+a', '/~haypepps/']

    for path in encoded:
      assert str(furl.Path(path)) == urllib.unquote(path)

    for path in unencoded:
      assert str(furl.Path(path)) == path

  def test_add(self):
    p = furl.Path('a/b/c/')
    assert p == p.add('d')
    assert str(p) == 'a/b/c/d'
    assert p == p.add('/')
    assert str(p) == 'a/b/c/d/'
    assert p == p.add(['e', 'f', 'e e', ''])
    assert str(p) == 'a/b/c/d/e/f/e e/'

  def test_set(self):
    p = furl.Path('a/b/c/')
    assert p == p.set('asdf/asdf/')
    assert str(p) == 'asdf/asdf/'
    assert p == p.set(['a', 'b', 'c', ''])
    assert str(p) == 'a/b/c/'

  def test_remove(self):
    p = furl.Path('a/b/s%20s/')
    assert p == p.remove(True)
    assert str(p) == ''

    p = furl.Path('a/b/s%20s/')
    assert p == p.remove(['b', 's s'])
    assert str(p) == 'a/'

    p = furl.Path('a/b/s%20s/')
    assert p == p.remove(['', 'b', 's s'])
    assert str(p) == 'a'


class TestPathCompositionInterface(unittest.TestCase):
  def test_interface(self):
    class tester(furl.PathCompositionInterface):
      def __init__(self):
        furl.PathCompositionInterface.__init__(self)

      def __setattr__(self, attr, value):
        if not furl.PathCompositionInterface.__setattr__(self, attr, value):
          object.__setattr__(self, attr, value)

    t = tester()
    assert isinstance(t.path, furl.Path)
    assert t.pathstr == ''

    t.path = 'asdf/asdf'
    assert t.pathstr == 'asdf/asdf'
    assert t.path.segments == ['asdf', 'asdf']
    assert not t.path.isabsolute


class TestQuery(unittest.TestCase):
  def test_basics(self):
    for query in ['', 'asdfasdf', '/asdf/asdf/sdf']:
      q = furl.Query(query)
      assert q.params == {}
      assert str(q) == ''

    q = furl.Query('=asdf')
    assert q.params == {'':'asdf'}
    assert str(q) == '=asdf'

    # URL encoding.
    q = furl.Query('space=a+a&amp=a%26a')
    assert q.params == {'space':'a a', 'amp':'a&a'}
    assert str(q) == 'space=a+a&amp=a%26a' or str(q) == 'amp=a%26a&space=a+a'

    q = furl.Query('space=a a&amp=a^a')
    assert q.params == {'space':'a a', 'amp':'a^a'}
    assert str(q) == 'space=a+a&amp=a%5Ea' or str(q) == 'amp=a%5Ea&space=a+a'

    # Duplicates are truncated.
    q = furl.Query('space=a+a&space=b+b')
    assert q.params == {'space':'a a'}
    assert str(q) == 'space=a+a'

  def test_params(self):
    q = furl.Query('a=a&b=b')
    assert q.params == {'a':'a', 'b':'b'}
    q.params['sup'] = 'sup'
    assert q.params == {'a':'a', 'b':'b', 'sup':'sup'}
    del q.params['a']
    assert q.params == {'b':'b', 'sup':'sup'}
    q.params['b'] = 'BLROP'
    assert q.params == {'b':'BLROP', 'sup':'sup'}

    # Non-string parameters are stringified
    q.params.clear()
    q.params[99] = 99
    q.params['int'] = 1
    q.params['float'] = 0.39393
    assert furl.parse_qs(str(q)) == {'int':'1', 'float':'0.39393', '99':'99'}

  def test_add(self):
    q = furl.Query('a=a')
    assert q == q.add({'b':'b', 's':'s s'})
    comps = furl.parse_qs(str(q))
    assert comps['a'] == 'a' and comps['b'] == 'b' and comps['s'] == 's s'

  def test_set(self):
    q = furl.Query('a=a')
    assert q == q.set({'b':'b', 's':'s s'})
    comps = furl.parse_qs(str(q))
    assert comps['b'] == 'b' and comps['s'] == 's s'

  def test_remove(self):
    q = furl.Query('a=a&b=b&s=s s')
    assert q == q.remove(['a', 'b'])
    assert str(q) == 's=s+s'

    assert q == q.remove(query=True)
    assert str(q) == ''


class TestQueryCompositionInterface(unittest.TestCase):
  def test_interface(self):
    class tester(furl.QueryCompositionInterface):
      def __init__(self):
        furl.QueryCompositionInterface.__init__(self)

      def __setattr__(self, attr, value):
        if not furl.QueryCompositionInterface.__setattr__(self, attr, value):
          object.__setattr__(self, attr, value)

    t = tester()
    assert isinstance(t.query, furl.Query)
    assert t.querystr == ''

    t.query = 'a=a&s=s s'
    assert t.querystr == 'a=a&s=s+s'
    assert t.args == t.query.params == {'a':'a', 's':'s s'}


class TestFragment(unittest.TestCase):
  def test_basics(self):
    f = furl.Fragment('')
    assert str(f.path) == '' and str(f.query) == '' and str(f) == ''

    f.args['sup'] = 'foo'
    assert str(f) == 'sup=foo'
    f.path = 'yasup'
    assert str(f) == 'yasup?sup=foo'
    f.path = '/yasup'
    assert str(f) == '/yasup?sup=foo'
    assert str(f.query) == f.querystr == 'sup=foo'
    f.query.params['sup'] = 'kwlpumps'
    assert str(f) == '/yasup?sup=kwlpumps'
    f.query = ''
    assert str(f) == '/yasup'
    f.path = ''
    assert str(f) == ''
    f.args['no'] = 'dads'
    f.query.params['hi'] = 'gr8job'
    assert str(f) == 'hi=gr8job&no=dads' or str(f) == 'no=dads&hi=higr8job'

  def test_add(self):
    f = furl.Fragment('')
    assert f == f.add(path='one two three', args={'a':'a', 's':'s s'})
    assert str(f) == 'one two three?a=a&s=s+s'

  def test_set(self):
    f = furl.Fragment('asdf?lol=sup&foo=blorp')
    assert f == f.set(path='one two three', args={'a':'a', 's':'s s'})
    assert str(f) == 'one two three?a=a&s=s+s'

    assert f == f.set(path='!', separator=False)
    assert f.separator == False
    assert str(f) == '!a=a&s=s+s'

  def test_remove(self):
    f = furl.Fragment('a/path/great/job?lol=sup&foo=blorp')
    assert f == f.remove(path='job', args=['lol'])
    assert str(f) == 'a/path/great/?foo=blorp'

    assert f == f.remove(path=['path', 'great'], args=['foo'])
    assert str(f) == 'a/'

    assert f == f.remove(fragment=True)
    assert str(f) == ''


class TestFragmentCompositionInterface(unittest.TestCase):
  def test_interface(self):
    class tester(furl.FragmentCompositionInterface):
      def __init__(self):
        furl.FragmentCompositionInterface.__init__(self)

      def __setattr__(self, attr, value):
        if not furl.FragmentCompositionInterface.__setattr__(self, attr, value):
          object.__setattr__(self, attr, value)

    t = tester()
    assert isinstance(t.fragment.path, furl.Path)
    assert isinstance(t.fragment.query, furl.Query)
    assert t.fragmentstr == ''
    assert t.fragment.separator
    assert t.fragment.pathstr == ''
    assert t.fragment.querystr == ''

    t.fragment.path = 'asdf/asdf'
    t.fragment.query = 'a=a&s=s s'
    assert t.fragment.pathstr == 'asdf/asdf'
    assert t.fragment.path.segments == ['asdf', 'asdf']
    assert not t.fragment.path.isabsolute
    assert t.fragment.querystr == 'a=a&s=s+s'
    assert t.fragment.args == t.fragment.query.params == {'a':'a', 's':'s s'}


class TestFurl(unittest.TestCase):
  def setUp(self):
    # Don't hide duplicate warnings - we want to test for them.
    warnings.simplefilter("always")

  def _param(self, url, key, val):
    # Note: urlparse.urlsplit() doesn't separate query from path for all
    # schemes, only those schemes in urlparse.uses_query. So this little helper
    # function will only work when provided urls whos schemes are also in
    # urlparse.uses_query.
    params = urlparse.parse_qs(urlparse.urlsplit(url).query)
    return key in params and params[key][0] == val

  def test_basics(self):
    url = 'hTtP://www.pumps.com/'
    fu = furl.furl(url)
    assert fu.scheme == 'http'
    assert fu.netloc == 'www.pumps.com'
    assert fu.host == 'www.pumps.com'
    assert fu.port == 80
    assert str(fu.path) == fu.pathstr == '/'
    assert str(fu.query) == fu.querystr  == ''
    assert fu.args == fu.query.params == {}
    assert str(fu.fragment) == fu.fragmentstr == ''
    assert fu.url == str(fu) == url.lower()

    url = 'HTTPS://wWw.YAHOO.cO.UK/one/two/three?a=a&b=b&m=m%26m#fragment'
    fu = furl.furl(url)
    assert fu.scheme == 'https'
    assert fu.netloc == 'www.yahoo.co.uk'
    assert fu.host == 'www.yahoo.co.uk'
    assert fu.port == 443
    assert fu.pathstr == str(fu.path) == '/one/two/three'
    assert fu.querystr == str(fu.query) == 'a=a&b=b&m=m%26m'
    assert fu.args == fu.query.params == {'a':'a', 'b':'b', 'm':'m&m'}
    assert str(fu.fragment) == fu.fragmentstr == 'fragment'
    assert fu.url == str(fu) == url.lower()

    url = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl%20string#frag'
    fu = furl.furl(url)
    assert fu.scheme == 'sup'
    assert fu.netloc == '192.168.1.102:8080'
    assert fu.host == '192.168.1.102'
    assert fu.port == 8080
    assert fu.pathstr == str(fu.path) == '///one//a b////'
    assert fu.querystr == str(fu.query) == 's=kwl+string'
    assert fu.args == fu.query.params == {'s':'kwl string'}
    assert str(fu.fragment) == fu.fragmentstr == 'frag'
    query_quoted = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl+string#frag'
    assert fu.url == str(fu) == query_quoted

  def test_basic_manipulation(self):
    fu = furl.furl('http://www.pumps.com/')

    fu.args.setdefault('foo', 'blah')
    assert str(fu) == 'http://www.pumps.com/?foo=blah'
    fu.query.params['foo'] = 'eep'
    assert str(fu) == 'http://www.pumps.com/?foo=eep'

    fu.port = 99
    assert str(fu) == 'http://www.pumps.com:99/?foo=eep'

    fu.netloc = 'www.yahoo.com:220'
    assert str(fu) == 'http://www.yahoo.com:220/?foo=eep'

    fu.netloc = 'www.yahoo.com'
    assert fu.port == 80
    assert str(fu) == 'http://www.yahoo.com/?foo=eep'

    fu.scheme = 'sup'
    assert str(fu) == 'sup://www.yahoo.com:80/?foo=eep'

    fu.port = None
    assert str(fu) == 'sup://www.yahoo.com/?foo=eep'

    fu.fragment = 'sup'
    assert str(fu) == 'sup://www.yahoo.com/?foo=eep#sup'

    fu.path = 'hay supppp'
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?foo=eep#sup'

    fu.args['space'] = '1 2'
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?foo=eep&space=1+2#sup'

    del fu.args['foo']
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?space=1+2#sup'

    fu.query = 'a=a&s=s*s'
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?a=a&s=s%2As#sup'

    fu.query = 'a=a&c=c%5Ec'
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?a=a&c=c%5Ec#sup'

    fu.query = {'pue':'pue', 'a':'a&a'}
    assert str(fu) == 'sup://www.yahoo.com/hay%20supppp?a=a%26a&pue=pue#sup'

    fu.host = 'ohay.com'
    assert str(fu) == 'sup://ohay.com/hay%20supppp?a=a%26a&pue=pue#sup'
    
  def test_odd_urls(self):
    # Empty.
    fu = furl.furl('')
    assert fu.scheme == ''
    assert fu.host == ''
    assert fu.port == None
    assert fu.netloc == ''
    assert fu.pathstr == str(fu.path) == ''
    assert fu.querystr == str(fu.query) == ''
    assert fu.args == fu.query.params == {}
    assert str(fu.fragment) == fu.fragmentstr == ''
    assert fu.url == ''

    # TODO(grun): Test more odd urls.

  def test_hosts(self):
    # No host.
    url = 'http:///index.html'
    assert furl.furl(url).url == url

    # Valid IPv4 and IPv6 addresses.
    fu = furl.furl('http://192.168.1.101')
    fu = furl.furl('http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/')

    # Invalid IPv4 shouldn't raise an exception because urlparse.urlsplit()
    # doesn't raise an exception on invalid IPv4 addresses.
    fu = furl.furl('http://1.2.3.4.5.6/')

    # Invalid IPv6 shouldn't raise an exception because urlparse.urlsplit()
    # doesn't raise an exception on invalid IPv6 addresses.
    furl.furl('http://[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]/')

    # Malformed IPv6 should raise an exception because urlparse.urlsplit()
    # raises an exception.
    with self.assertRaises(ValueError):
      furl.furl('http://[0:0:0:0:0:0:0:1/')
    with self.assertRaises(ValueError):
      furl.furl('http://0:0:0:0:0:0:0:1]/')

  def test_netlocs(self):
    fu = furl.furl('http://pumps.com/')
    netloc = '1.2.3.4.5.6:999'
    fu.netloc = netloc
    assert fu.netloc == netloc
    assert fu.host == '1.2.3.4.5.6'
    assert fu.port == 999

    netloc = '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]:888'
    fu.netloc = netloc
    assert fu.netloc == netloc
    assert fu.host == '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]'
    assert fu.port == 888

    # Malformed IPv6 should raise an exception because urlparse.urlsplit()
    # raises an exception.
    with self.assertRaises(ValueError):
      fu.netloc = '[0:0:0:0:0:0:0:1'
    with self.assertRaises(ValueError):
      fu.netloc = '0:0:0:0:0:0:0:1]'

    # Invalid ports.
    with self.assertRaises(ValueError):
      fu.netloc = '[0:0:0:0:0:0:0:1]:alksdflasdfasdf'
    with self.assertRaises(ValueError):
      fu.netloc = 'pump2pump.org:777777777777'

    # No side effects.
    assert fu.host == '[0:0:0:0:0:0:0:1:1:1:1:1:1:1:1:9999999999999]'
    assert fu.port == 888

  def test_ports(self):
    # Default port values.
    assert furl.furl('http://www.pumps.com/').port == 80
    assert furl.furl('https://www.pumps.com/').port == 443
    assert furl.furl('undefined://www.pumps.com/').port == None

    # Override default port values.
    assert furl.furl('http://www.pumps.com:9000/').port == 9000
    assert furl.furl('https://www.pumps.com:9000/').port == 9000
    assert furl.furl('undefined://www.pumps.com:9000/').port == 9000

    # Reset the port.
    fu = furl.furl('http://www.pumps.com:9000/')
    fu.port = None
    assert fu.url == 'http://www.pumps.com/'
    assert fu.port == 80

    fu = furl.furl('undefined://www.pumps.com:9000/')
    fu.port = None
    assert fu.url == 'undefined://www.pumps.com/'
    assert fu.port == None
    
    # Invalid port raises ValueError with no side effects.
    with self.assertRaises(ValueError):
      furl.furl('http://www.pumps.com:invalid/')

    url = 'http://www.pumps.com:400/'
    fu = furl.furl(url)
    assert fu.port == 400
    with self.assertRaises(ValueError):
      fu.port = 'asdf'
    assert fu.url == url
    fu.port = 9999
    with self.assertRaises(ValueError):
      fu.port = []
    with self.assertRaises(ValueError):
      fu.port = -1
    with self.assertRaises(ValueError):
      fu.port = 77777777777
    assert fu.port == 9999
    assert fu.url == 'http://www.pumps.com:9999/'

    self.assertRaises(fu.set, port='asdf')

  def test_add(self):
    fu = furl.furl('http://pumps.com/')

    assert fu == fu.add(args={'a':'a', 'm':'m&m'}, path='/kwl jump',
                        fragment_path='1', fragment_args={'f':'frp'})
    assert self._param(fu.url, 'a', 'a')
    assert self._param(fu.url, 'm', 'm&m')
    assert str(fu.fragment) == fu.fragmentstr == '1?f=frp'
    assert urlparse.urlsplit(fu.url).path == '/kwl%20jump'

    assert fu == fu.add(path='dir', fragment_path='23', args={'b':'b'},
                        fragment_args={'b':'bewp'})
    assert self._param(fu.url, 'a', 'a')
    assert self._param(fu.url, 'm', 'm&m')
    assert self._param(fu.url, 'b', 'b')
    assert fu.pathstr == str(fu.path) == '/kwl jump/dir'
    assert str(fu.fragment) == fu.fragmentstr == '1/23?b=bewp&f=frp'

    # Test warnings for potentially overlapping parameters.
    with warnings.catch_warnings(True) as w1:
      fu.add(args={'a':'1'}, query_params={'a':'2'})
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
      assert self._param(fu.url, 'a', '2') # <query_params> takes precedence.

  def test_set(self):
    fu = furl.furl('http://pumps.com/kwl%20jump/dir')
    assert fu == fu.set(args={'no':'nope'}, fragment='sup')
    assert 'a' not in fu.args
    assert 'b' not in fu.args
    assert fu.url == 'http://pumps.com/kwl%20jump/dir?no=nope#sup'

    # No conflict warnings between <host>/<port> and <netloc>, or <query> and
    # <params>.
    assert fu == fu.set(args={'a':'a a'}, path='path path/dir', port='999',
                        fragment='moresup', scheme='sup', host='host')
    assert fu.url == 'sup://host:999/path%20path/dir?a=a+a#moresup'

    # Path as a list of paths to join.
    assert fu == fu.set(path=['d1', 'd2'])
    assert fu.url == 'sup://host:999/d1/d2?a=a+a#moresup'
    assert fu == fu.add(path=['/d3/', '/d4/'])
    assert fu.url == 'sup://host:999/d1/d2//d3///d4/?a=a+a#moresup'

    # Set a lot of stuff (but avoid conflicts, which are tested below).
    fu.set(query_params={'k':'k'}, fragment_path='no scrubs', scheme='morp',
           host='myhouse', port=69, path='j$j*m#n', fragment_args={'f':'f'})
    assert fu.url == 'morp://myhouse:69/j%24j%2Am%23n?k=k#no scrubs?f=f'

    # No side effects.
    oldurl = fu.url
    self.assertRaises(ValueError, fu.set, args={'a':'a a'},
                      path='path path/dir', port='INVALID_PORT',
                      fragment='moresup', scheme='sup', host='host')
    assert fu.url == oldurl
    with warnings.catch_warnings(True) as w1:
      self.assertRaises(ValueError, fu.set, netloc='nope.com:99', port='NOPE')
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
    assert fu.url == oldurl

    # Test warnings for potentially overlapping parameters.
    fu = furl.furl('http://pumps.com')
    warnings.simplefilter("always")

    # Host, port, and netloc overlap - host and port take precedence.
    with warnings.catch_warnings(True) as w1:
      fu.set(netloc='dumps.com:99', host='ohay.com')
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
      fu.host == 'ohay.com'
      fu.port == 99
    with warnings.catch_warnings(True) as w2:
      fu.set(netloc='dumps.com:99', port=88)
      assert len(w2) == 1 and issubclass(w2[0].category, UserWarning)
      fu.port == 88
    with warnings.catch_warnings(True) as w3:
      fu.set(netloc='dumps.com:99', host='ohay.com', port=88)
      assert len(w3) == 1 and issubclass(w3[0].category, UserWarning)

    # Query, args, and query_params overlap - args and query_params take
    # precedence.
    with warnings.catch_warnings(True) as w4:
      fu.set(query='yosup', args={'a':'a', 'b':'b'})
      assert len(w4) == 1 and issubclass(w4[0].category, UserWarning)
      assert self._param(fu.url, 'a', 'a')
      assert self._param(fu.url, 'b', 'b')
    with warnings.catch_warnings(True) as w5:
      fu.set(query='yosup', query_params={'a':'a', 'b':'b'})
      assert len(w5) == 1 and issubclass(w5[0].category, UserWarning)
      assert self._param(fu.url, 'a', 'a')
      assert self._param(fu.url, 'b', 'b')
    with warnings.catch_warnings(True) as w6:
      fu.set(args={'a':'a', 'b':'b'}, query_params={'c':'c', 'd':'d'})
      assert len(w6) == 1 and issubclass(w6[0].category, UserWarning)
      assert self._param(fu.url, 'c', 'c')
      assert self._param(fu.url, 'd', 'd')

    # Fragment, fragment_path, fragment_args, and fragment_separator overlap -
    # fragment_separator, fragment_path, and fragment_args take precedence.
    with warnings.catch_warnings(True) as w7:
      fu.set(fragment='hi', fragment_path='!', fragment_args={'a':'a'},
             fragment_separator=False)
      assert len(w7) == 1 and issubclass(w7[0].category, UserWarning)
      assert str(fu.fragment) == '!a=a'
    with warnings.catch_warnings(True) as w8:
      fu.set(fragment='hi', fragment_path='bye')
      assert len(w8) == 1 and issubclass(w8[0].category, UserWarning)
      assert str(fu.fragment) == 'bye'
    with warnings.catch_warnings(True) as w9:
      fu.set(fragment='hi', fragment_args={'a':'a'})
      assert len(w9) == 1 and issubclass(w9[0].category, UserWarning)
      print fu.fragmentstr
      assert str(fu.fragment) == 'hi?a=a'
    with warnings.catch_warnings(True) as w10:
      fu.set(fragment='!?a=a', fragment_separator=False)
      assert len(w10) == 1 and issubclass(w10[0].category, UserWarning)
      assert str(fu.fragment) == '!a=a'

  def test_remove(self):
    url = 'http://host:69/a/big/path/?a=a&b=b&s=s+s#a frag?with=args&a=a'
    
    fu = furl.furl(url)
    assert fu == fu.remove(fragment=True, args=['a', 'b'], path='path',
                           port=True)
    assert fu.url == 'http://host/a/big/?s=s+s'

    # No errors are thrown when removing url components that don't exist.
    fu = furl.furl(url)
    assert fu == fu.remove(fragment_path=['asdf'], fragment_args=['asdf'],
                           args=['asdf'], path=['ppp', 'ump'])
    assert self._param(fu.url, 'a', 'a')
    assert self._param(fu.url, 'b', 'b')
    assert self._param(fu.url, 's', 's s')
    assert fu.pathstr == '/a/big/path/'
    assert fu.fragment.pathstr == 'a frag'
    assert fu.fragment.args == {'a':'a', 'with':'args'}

    # Path as a list of paths to join before removing.
    assert fu == fu.remove(fragment_path='a frag', fragment_args=['a'],
                           query_params=['a','b'], path=['big', 'path'],
                           port=True)
    assert fu.url == 'http://host/a/?s=s+s#with=args'

    assert fu == fu.remove(path=True, query=True, fragment=True)
    assert fu.url == 'http://host'

  def test_parse_qs(self):
    assert furl.parse_qs('a=a&b=b') == {'a':'a', 'b':'b'}

    # Duplicates are truncated.
    assert furl.parse_qs('a=a&b=b&a=c') == {'a':'a', 'b':'b'}

    # URL encoding.
    assert furl.parse_qs('space=a+a&amp=a%26a') == {'space':'a a', 'amp':'a&a'}

  def test_urlsplit(self):
    # No changes to existing urlsplit() behavior for known schemes.
    url = 'http://www.pumps.com/'
    assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
    assert furl.urlsplit(url) == urlparse.urlsplit(url)

    url = 'https://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
    assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
    assert furl.urlsplit(url) == urlparse.urlsplit(url)

    # Properly split the query from the path for unknown schemes.
    url = 'sup://192.168.1.102:8080///one//two////?s=kwl%20string#frag'
    correct = ('sup', '192.168.1.102:8080', '///one//two////',
               's=kwl%20string', 'frag')
    assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
    assert furl.urlsplit(url) == correct

    url = 'crazyyyyyy://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
    correct = ('crazyyyyyy', 'www.yahoo.co.uk', '/one/two/three',
               'a=a&b=b&m=m%26m', 'fragment')
    assert isinstance(furl.urlsplit(url), urlparse.SplitResult)
    assert furl.urlsplit(url) == correct
          
  def test_url_path_join(self):
    # Basics.
    assert furl.url_path_join() == ''
    assert furl.url_path_join('/', '') == '/'
    assert furl.url_path_join('a') == 'a'
    assert furl.url_path_join('/a') == '/a'
    assert furl.url_path_join('/a/') == '/a/'
    assert furl.url_path_join('///////a///////') == '/a/'
    assert furl.url_path_join('/a', '') == '/a/'

    # Slashes.
    assert furl.url_path_join('/', '') == '/'
    assert furl.url_path_join('/', '/') == '/'
    assert furl.url_path_join('/', '/', '/') == '/'

    # Multiple paths to join.
    assert furl.url_path_join('a', 'b', 'c') == 'a/b/c'
    assert furl.url_path_join('/a/', '/b/', '/c') == '/a/b/c'
    assert furl.url_path_join('/a/', '/b/', '/c/') == '/a/b/c/'
    assert furl.url_path_join('//////a/', '/b/////', '/c/////') == '/a/b/c/'
    assert furl.url_path_join('a b', 'c d') == 'a b/c d'
    assert furl.url_path_join('a%20b', 'c%20d') == 'a%20b/c%20d'
    assert furl.url_path_join('a', 'b', 'c', 'd', 'e', 'f') == 'a/b/c/d/e/f'
    assert furl.url_path_join('/a', 'b', 'c', 'd', 'e', 'f') == '/a/b/c/d/e/f'
    assert furl.url_path_join('/a', 'b', 'c', 'd', 'e', 'f/') == '/a/b/c/d/e/f/'

  def test_url_path_remove(self):
    # Basics.
    assert furl.url_path_remove('', '') == ''
    assert furl.url_path_remove('', '/') == ''
    assert furl.url_path_remove('', 'asdf') == ''
    assert furl.url_path_remove('', 'gr8pants/gr8pants') == ''
    assert furl.url_path_remove('', '/gr8pants/gr8pants') == ''
    assert furl.url_path_remove('/', '') == '/'
    assert furl.url_path_remove('/', 'asdf') == '/'
    assert furl.url_path_remove('/', 'gr8pants/gr8pants') == '/'
    assert furl.url_path_remove('/', '/gr8pants/gr8pants') == '/'

    # Slash manipulation.
    assert furl.url_path_remove('/', '/') == ''
    assert furl.url_path_remove('a/', '/') == 'a'
    assert furl.url_path_remove('a/b', 'b') == 'a/'
    assert furl.url_path_remove('a/b', '/b') == 'a'
    assert furl.url_path_remove('a/b/', '/') == 'a/b'
    assert furl.url_path_remove('/a/', '/') == '/a'
    assert furl.url_path_remove('/a/b', 'b') == '/a/'
    assert furl.url_path_remove('/a/b', '/b') == '/a'
    assert furl.url_path_remove('/a/b', 'b/') == '/a/'
    assert furl.url_path_remove('/a/b/', '/') == '/a/b'
    assert furl.url_path_remove('/a/b/', 'b') == '/a/'

    # Remove a portion of the path from the tail of the original path.
    assert furl.url_path_remove('/a/b/c', 'b/c') == '/a/'
    assert furl.url_path_remove('/a/b/c', '/b/c') == '/a'
    assert furl.url_path_remove('/a/b c/d/', 'b c/d/') == '/a/'
    assert furl.url_path_remove('/a/b c/d/', '/b c/d/') == '/a'
    assert furl.url_path_remove('/a/b%20c/d/', 'b%20c/d/') == '/a/'
    assert furl.url_path_remove('/a/b%20c/d/', '/b%20c/d/') == '/a'
    assert furl.url_path_remove('/a/b/c/', 'b/c') == '/a/'
    assert furl.url_path_remove('/a/b/c/', '/b/c') == '/a'
    assert furl.url_path_remove('/a/b/c/', 'b/c/') == '/a/'
    assert furl.url_path_remove('/a/b/c/', '/b/c/') == '/a'
    assert furl.url_path_remove('/a/b/c', '/a/b/c') == ''
    assert furl.url_path_remove('/a/b/c/', '/a/b/c/') == ''
    assert furl.url_path_remove('/a/b/c/', '/a/b/c') == '/'

    # Attempt to remove valid subsections, but subsections not from the end of
    # the original path.
    assert furl.url_path_remove('a/b/c', 'a/b') == 'a/b/c'
    assert furl.url_path_remove('a/b/c', 'a/b/') == 'a/b/c'
    assert furl.url_path_remove('a/b/c', '/a/b/') == 'a/b/c'
    assert furl.url_path_remove('/a/b/c', 'a/b') == '/a/b/c'
    assert furl.url_path_remove('/a/b/c', 'a/b/') == '/a/b/c'
    assert furl.url_path_remove('/a/b/c', '/a/b/') == '/a/b/c'

  def test_isvalidport(self):
    valids = [1, 2, 3, 65535, 119, 2930]
    invalids = [-1, 0, 'a', [], (0), {1:1}, 65536, 99999]

    for port in valids:
      assert furl.isvalidport(port)
    for port in invalids:
      assert not furl.isvalidport(port)
