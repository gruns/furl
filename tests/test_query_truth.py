# -*- coding: utf-8 -*-

import unittest

from furl import Query, furl


class UncheckedList(list):
    def __bool__(self):
        raise ValueError('query inputs must not be truth-tested')

    __nonzero__ = __bool__


class FalseList(list):
    def __bool__(self):
        return False

    __nonzero__ = __bool__


class UncheckedDict(dict):
    def __bool__(self):
        raise ValueError('query inputs must not be truth-tested')

    __nonzero__ = __bool__


class FalseDict(dict):
    def __bool__(self):
        return False

    __nonzero__ = __bool__


class TestQueryTruth(unittest.TestCase):
    pairs = [('page', '2'), ('sort', 'name')]
    containers = (UncheckedList, FalseList, UncheckedDict, FalseDict)

    def test_constructor(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                query = Query(container(self.pairs))
                self.assertEqual(query.params.allitems(), self.pairs)

    def test_load(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                query = Query('old=1')
                self.assertIs(query.load(container(self.pairs)), query)
                self.assertEqual(query.params.allitems(), self.pairs)

    def test_add(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                query = Query('old=1')
                self.assertIs(query.add(container(self.pairs)), query)
                self.assertEqual(query.params.allitems(),
                                 [('old', '1')] + self.pairs)

    def test_params_assignment(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                query = Query('old=1')
                original = query.params
                query.params = container(self.pairs)
                self.assertIs(query.params, original)
                self.assertEqual(query.params.allitems(), self.pairs)

    def test_url_constructor(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                url = furl('https://example.com', args=container(self.pairs))
                self.assertEqual(url.args.allitems(), self.pairs)
                self.assertEqual(url.url,
                                 'https://example.com?page=2&sort=name')

    def test_url_assignment(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                url = furl('https://example.com?old=1')
                url.args = container(self.pairs)
                self.assertEqual(url.args.allitems(), self.pairs)

    def test_empty_iterable_inputs(self):
        for container in self.containers:
            with self.subTest(container=container.__name__):
                self.assertEqual(Query(container()).params.allitems(), [])

    def test_existing_empty_inputs(self):
        for value in (None, '', b'', False, 0, [], (), {}):
            with self.subTest(value=value):
                self.assertEqual(Query(value).params.allitems(), [])

    def test_duplicate_keys_and_generator(self):
        pairs = [('a', '1'), ('b', '2'), ('a', '3')]
        for container in (UncheckedList, FalseList, iter):
            with self.subTest(container=container.__name__):
                query = Query(container(pairs))
                self.assertEqual(query.params.allitems(), pairs)
                self.assertEqual(query.encode(), 'a=1&b=2&a=3')
