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

import urllib.request, urllib.parse, urllib.error
import unittest
import urllib.parse
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
      assert str(furl.Path(path)) == urllib.parse.unquote(path)

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
    params = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    return key in params and params[key][0] == val

  def test_username_and_password(self):
    # Empty usernames and passwords.
    for url in ['', 'http://www.pumps.com/']:
      f = furl.furl(url)
      assert not f.username and not f.password

    usernames = ['user', 'a-user_NAME$%^&09']
    passwords = ['pass', 'a-PASS_word$%^&09']
    baseurl = 'http://www.google.com/'
    
    # Username only.
    userurl = 'http://%s@www.google.com/'
    for username in usernames:
      f = furl.furl(userurl % username)
      assert f.username == username and not f.password

      f = furl.furl(baseurl)
      f.username = username
      assert f.username == username and not f.password
      assert f.url == userurl % username

      f = furl.furl(baseurl)
      f.set(username=username)
      assert f.username == username and not f.password
      assert f.url == userurl % username

      f.remove(username=True)
      assert not f.username and not f.password
      assert f.url == baseurl

    # Password only.
    passurl = 'http://:%s@www.google.com/'
    for password in passwords:
      f = furl.furl(passurl % password)
      assert f.password == password and f.username == ''

      f = furl.furl(baseurl)
      f.password = password
      assert f.password == password and f.username == ''
      assert f.url == passurl % password

      f = furl.furl(baseurl)
      f.set(password=password)
      assert f.password == password and f.username == ''
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

    # Through network location.
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

  def test_basics(self):
    url = 'hTtP://www.pumps.com/'
    f = furl.furl(url)
    assert f.scheme == 'http'
    assert f.netloc == 'www.pumps.com'
    assert f.host == 'www.pumps.com'
    assert f.port == 80
    assert str(f.path) == f.pathstr == '/'
    assert str(f.query) == f.querystr  == ''
    assert f.args == f.query.params == {}
    assert str(f.fragment) == f.fragmentstr == ''
    assert f.url == str(f) == url.lower()

    url = 'HTTPS://wWw.YAHOO.cO.UK/one/two/three?a=a&b=b&m=m%26m#fragment'
    f = furl.furl(url)
    assert f.scheme == 'https'
    assert f.netloc == 'www.yahoo.co.uk'
    assert f.host == 'www.yahoo.co.uk'
    assert f.port == 443
    assert f.pathstr == str(f.path) == '/one/two/three'
    assert f.querystr == str(f.query) == 'a=a&b=b&m=m%26m'
    assert f.args == f.query.params == {'a':'a', 'b':'b', 'm':'m&m'}
    assert str(f.fragment) == f.fragmentstr == 'fragment'
    assert f.url == str(f) == url.lower()

    url = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl%20string#frag'
    f = furl.furl(url)
    assert f.scheme == 'sup'
    assert f.netloc == '192.168.1.102:8080'
    assert f.host == '192.168.1.102'
    assert f.port == 8080
    assert f.pathstr == str(f.path) == '///one//a b////'
    assert f.querystr == str(f.query) == 's=kwl+string'
    assert f.args == f.query.params == {'s':'kwl string'}
    assert str(f.fragment) == f.fragmentstr == 'frag'
    query_quoted = 'sup://192.168.1.102:8080///one//a%20b////?s=kwl+string#frag'
    assert f.url == str(f) == query_quoted

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
    assert str(f) == 'sup://www.yahoo.com/hay%20supppp?foo=eep&space=1+2#sup'

    del f.args['foo']
    assert str(f) == 'sup://www.yahoo.com/hay%20supppp?space=1+2#sup'

    f.query = 'a=a&s=s*s'
    assert str(f) == 'sup://www.yahoo.com/hay%20supppp?a=a&s=s%2As#sup'

    f.query = 'a=a&c=c%5Ec'
    assert str(f) == 'sup://www.yahoo.com/hay%20supppp?a=a&c=c%5Ec#sup'

    f.query = {'pue':'pue', 'a':'a&a'}
    assert str(f) == 'sup://www.yahoo.com/hay%20supppp?a=a%26a&pue=pue#sup'

    f.host = 'ohay.com'
    assert str(f) == 'sup://ohay.com/hay%20supppp?a=a%26a&pue=pue#sup'
    
  def test_odd_urls(self):
    # Empty.
    f = furl.furl('')
    assert f.scheme == ''
    assert f.host == ''
    assert f.port == None
    assert f.netloc == ''
    assert f.pathstr == str(f.path) == ''
    assert f.querystr == str(f.query) == ''
    assert f.args == f.query.params == {}
    assert str(f.fragment) == f.fragmentstr == ''
    assert f.url == ''

    # TODO(grun): Test more odd urls.

  def test_hosts(self):
    # No host.
    url = 'http:///index.html'
    assert furl.furl(url).url == url

    # Valid IPv4 and IPv6 addresses.
    f = furl.furl('http://192.168.1.101')
    f = furl.furl('http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/')

    # Invalid IPv4 shouldn't raise an exception because urlparse.urlsplit()
    # doesn't raise an exception on invalid IPv4 addresses.
    f = furl.furl('http://1.2.3.4.5.6/')

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

    # Malformed IPv6 should raise an exception because urlparse.urlsplit()
    # raises an exception.
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
    assert furl.furl('undefined://www.pumps.com/').port == None

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
    assert f.port == None
    
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

    assert f == f.add(args={'a':'a', 'm':'m&m'}, path='/kwl jump',
                        fragment_path='1', fragment_args={'f':'frp'})
    assert self._param(f.url, 'a', 'a')
    assert self._param(f.url, 'm', 'm&m')
    assert str(f.fragment) == f.fragmentstr == '1?f=frp'
    assert urllib.parse.urlsplit(f.url).path == '/kwl%20jump'

    assert f == f.add(path='dir', fragment_path='23', args={'b':'b'},
                        fragment_args={'b':'bewp'})
    assert self._param(f.url, 'a', 'a')
    assert self._param(f.url, 'm', 'm&m')
    assert self._param(f.url, 'b', 'b')
    assert f.pathstr == str(f.path) == '/kwl jump/dir'
    assert str(f.fragment) == f.fragmentstr == '1/23?b=bewp&f=frp'

    # Test warnings for potentially overlapping parameters.
    with warnings.catch_warnings(record=True) as w1:
      f.add(args={'a':'1'}, query_params={'a':'2'})
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
      assert self._param(f.url, 'a', '2') # <query_params> takes precedence.

  def test_set(self):
    f = furl.furl('http://pumps.com/kwl%20jump/dir')
    assert f == f.set(args={'no':'nope'}, fragment='sup')
    assert 'a' not in f.args
    assert 'b' not in f.args
    assert f.url == 'http://pumps.com/kwl%20jump/dir?no=nope#sup'

    # No conflict warnings between <host>/<port> and <netloc>, or <query> and
    # <params>.
    assert f == f.set(args={'a':'a a'}, path='path path/dir', port='999',
                        fragment='moresup', scheme='sup', host='host')
    assert f.url == 'sup://host:999/path%20path/dir?a=a+a#moresup'

    # Path as a list of paths to join.
    assert f == f.set(path=['d1', 'd2'])
    assert f.url == 'sup://host:999/d1/d2?a=a+a#moresup'
    assert f == f.add(path=['/d3/', '/d4/'])
    assert f.url == 'sup://host:999/d1/d2//d3///d4/?a=a+a#moresup'

    # Set a lot of stuff (but avoid conflicts, which are tested below).
    f.set(query_params={'k':'k'}, fragment_path='no scrubs', scheme='morp',
           host='myhouse', port=69, path='j$j*m#n', fragment_args={'f':'f'})
    assert f.url == 'morp://myhouse:69/j%24j%2Am%23n?k=k#no scrubs?f=f'

    # No side effects.
    oldurl = f.url
    self.assertRaises(ValueError, f.set, args={'a':'a a'},
                      path='path path/dir', port='INVALID_PORT',
                      fragment='moresup', scheme='sup', host='host')
    assert f.url == oldurl
    with warnings.catch_warnings(record=True) as w1:
      self.assertRaises(ValueError, f.set, netloc='nope.com:99', port='NOPE')
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
    assert f.url == oldurl

    # Test warnings for potentially overlapping parameters.
    f = furl.furl('http://pumps.com')
    warnings.simplefilter("always")

    # Host, port, and netloc overlap - host and port take precedence.
    with warnings.catch_warnings(record=True) as w1:
      f.set(netloc='dumps.com:99', host='ohay.com')
      assert len(w1) == 1 and issubclass(w1[0].category, UserWarning)
      f.host == 'ohay.com'
      f.port == 99
    with warnings.catch_warnings(record=True) as w2:
      f.set(netloc='dumps.com:99', port=88)
      assert len(w2) == 1 and issubclass(w2[0].category, UserWarning)
      f.port == 88
    with warnings.catch_warnings(record=True) as w3:
      f.set(netloc='dumps.com:99', host='ohay.com', port=88)
      assert len(w3) == 1 and issubclass(w3[0].category, UserWarning)

    # Query, args, and query_params overlap - args and query_params take
    # precedence.
    with warnings.catch_warnings(record=True) as w4:
      f.set(query='yosup', args={'a':'a', 'b':'b'})
      assert len(w4) == 1 and issubclass(w4[0].category, UserWarning)
      assert self._param(f.url, 'a', 'a')
      assert self._param(f.url, 'b', 'b')
    with warnings.catch_warnings(record=True) as w5:
      f.set(query='yosup', query_params={'a':'a', 'b':'b'})
      assert len(w5) == 1 and issubclass(w5[0].category, UserWarning)
      assert self._param(f.url, 'a', 'a')
      assert self._param(f.url, 'b', 'b')
    with warnings.catch_warnings(record=True) as w6:
      f.set(args={'a':'a', 'b':'b'}, query_params={'c':'c', 'd':'d'})
      assert len(w6) == 1 and issubclass(w6[0].category, UserWarning)
      assert self._param(f.url, 'c', 'c')
      assert self._param(f.url, 'd', 'd')

    # Fragment, fragment_path, fragment_args, and fragment_separator overlap -
    # fragment_separator, fragment_path, and fragment_args take precedence.
    with warnings.catch_warnings(record=True) as w7:
      f.set(fragment='hi', fragment_path='!', fragment_args={'a':'a'},
             fragment_separator=False)
      assert len(w7) == 1 and issubclass(w7[0].category, UserWarning)
      assert str(f.fragment) == '!a=a'
    with warnings.catch_warnings(record=True) as w8:
      f.set(fragment='hi', fragment_path='bye')
      assert len(w8) == 1 and issubclass(w8[0].category, UserWarning)
      assert str(f.fragment) == 'bye'
    with warnings.catch_warnings(record=True) as w9:
      f.set(fragment='hi', fragment_args={'a':'a'})
      assert len(w9) == 1 and issubclass(w9[0].category, UserWarning)
##      print(f.fragmentstr)
      assert str(f.fragment) == 'hi?a=a'
    with warnings.catch_warnings(record=True) as w10:
      f.set(fragment='!?a=a', fragment_separator=False)
      assert len(w10) == 1 and issubclass(w10[0].category, UserWarning)
      assert str(f.fragment) == '!a=a'

  def test_remove(self):
    url = 'http://host:69/a/big/path/?a=a&b=b&s=s+s#a frag?with=args&a=a'
    
    f = furl.furl(url)
    assert f == f.remove(fragment=True, args=['a', 'b'], path='path',
                           port=True)
    assert f.url == 'http://host/a/big/?s=s+s'

    # No errors are thrown when removing url components that don't exist.
    f = furl.furl(url)
    assert f == f.remove(fragment_path=['asdf'], fragment_args=['asdf'],
                           args=['asdf'], path=['ppp', 'ump'])
    assert self._param(f.url, 'a', 'a')
    assert self._param(f.url, 'b', 'b')
    assert self._param(f.url, 's', 's s')
    assert f.pathstr == '/a/big/path/'
    assert f.fragment.pathstr == 'a frag'
    assert f.fragment.args == {'a':'a', 'with':'args'}

    # Path as a list of paths to join before removing.
    assert f == f.remove(fragment_path='a frag', fragment_args=['a'],
                           query_params=['a','b'], path=['big', 'path'],
                           port=True)
    assert f.url == 'http://host/a/?s=s+s#with=args'

    assert f == f.remove(path=True, query=True, fragment=True)
    assert f.url == 'http://host'

  def test_parse_qs(self):
    assert furl.parse_qs('a=a&b=b') == {'a':'a', 'b':'b'}

    # Duplicates are truncated.
    assert furl.parse_qs('a=a&b=b&a=c') == {'a':'a', 'b':'b'}

    # URL encoding.
    assert furl.parse_qs('space=a+a&amp=a%26a') == {'space':'a a', 'amp':'a&a'}

  def test_urlsplit(self):
    # No changes to existing urlsplit() behavior for known schemes.
    url = 'http://www.pumps.com/'
    assert isinstance(furl.urlsplit(url), urllib.parse.SplitResult)
    assert furl.urlsplit(url) == urllib.parse.urlsplit(url)

    url = 'https://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
    assert isinstance(furl.urlsplit(url), urllib.parse.SplitResult)
    assert furl.urlsplit(url) == urllib.parse.urlsplit(url)

    # Properly split the query from the path for unknown schemes.
    url = 'sup://192.168.1.102:8080///one//two////?s=kwl%20string#frag'
    correct = ('sup', '192.168.1.102:8080', '///one//two////',
               's=kwl%20string', 'frag')
    assert isinstance(furl.urlsplit(url), urllib.parse.SplitResult)
    assert furl.urlsplit(url) == correct

    url = 'crazyyyyyy://www.yahoo.co.uk/one/two/three?a=a&b=b&m=m%26m#fragment'
    correct = ('crazyyyyyy', 'www.yahoo.co.uk', '/one/two/three',
               'a=a&b=b&m=m%26m', 'fragment')
    assert isinstance(furl.urlsplit(url), urllib.parse.SplitResult)
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
