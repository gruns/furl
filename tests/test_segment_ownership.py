import unittest

from furl import Path


class SegmentOwnershipTests(unittest.TestCase):
    def test_loading_does_not_remove_caller_segments(self):
        segments = ['', 'a', 'b']
        first = Path(segments)
        second = Path(segments)
        self.assertEqual(segments, ['', 'a', 'b'])
        self.assertEqual(str(first), '/a/b')
        self.assertEqual(str(second), '/a/b')

    def test_loaded_segments_are_independent(self):
        source = Path('/a')
        copied = Path(source)
        copied.segments.append('b')
        self.assertEqual(str(source), '/a')
        segments = ['a']
        copied = Path(segments)
        copied.segments.append('b')
        self.assertEqual(segments, ['a'])

    def test_adding_to_root_does_not_mutate_source_path(self):
        source = Path('/a')
        destination = Path('/')
        destination.add(source)
        self.assertEqual(str(destination), '/a')
        self.assertEqual(str(source), '/a')

    def test_adding_to_root_does_not_mutate_segment_list(self):
        segments = ['a']
        destination = Path('/')
        destination.add(segments)
        self.assertEqual(str(destination), '/a')
        self.assertEqual(segments, ['a'])
