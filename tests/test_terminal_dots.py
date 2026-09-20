import unittest

from furl import Path, furl


class TerminalDotTests(unittest.TestCase):
    def test_normalized_paths_keep_directory_semantics(self):
        cases = [
            ('/a/b/.', '/a/b/'),
            ('/a/b/..', '/a/'),
            ('a/b/.', 'a/b/'),
            ('a/b/..', 'a/'),
            ('/a/..', '/'),
            ('a/..', './'),
            ('/a/b...', '/a/b...'),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                path = Path(source)
                self.assertIs(path.normalize(), path)
                self.assertEqual(str(path), expected)
                self.assertEqual(str(path.normalize()), expected)

    def test_normalizing_before_join_keeps_parent_directory(self):
        value = furl('https://example.com/a/b/c/d/..')
        value.path.normalize()
        self.assertEqual(str(value.join('D')), 'https://example.com/a/b/c/D')
