#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# furl - URL manipulation made simple.
#
# Ansgar Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: Build Amazing Things (Unlicense)
#

import os
import sys
from os.path import dirname, join as pjoin
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand


meta = {}
with open(pjoin('furl', '__version__.py')) as f:
    exec(f.read(), meta)


class Publish(Command):
    """Publish to PyPI with twine."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('python setup.py sdist bdist_wheel')

        sdist = 'dist/furl-%s.tar.gz' % meta['__version__']
        wheel = 'dist/furl-%s-py2.py3-none-any.whl' % meta['__version__']
        rc = os.system('twine upload "%s" "%s"' % (sdist, wheel))

        sys.exit(rc)


class RunTests(TestCommand):
    """
    Run the unit tests.

    By default, `python setup.py test` fails if tests/ isn't a Python
    module; i.e. if the tests/ directory doesn't contain an __init__.py
    file). But the tests/ directory shouldn't contain an __init__.py
    file and tests/ shouldn't be a Python module. See

      http://doc.pytest.org/en/latest/goodpractices.html

    Running the unit tests manually here enables `python setup.py test`
    without tests/ being a Python module.
    """
    def run_tests(self):
        from unittest import TestLoader, TextTestRunner
        tests_dir = pjoin(dirname(__file__), 'tests/')
        suite = TestLoader().discover(tests_dir)
        result = TextTestRunner().run(suite)
        sys.exit(0 if result.wasSuccessful() else -1)


setup(
    name=meta['__title__'],
    license=meta['__license__'],
    version=meta['__version__'],
    author=meta['__author__'],
    author_email=meta['__contact__'],
    url=meta['__url__'],
    description=meta['__description__'],
    long_description=(
        'Information and documentation can be found at '
        'https://github.com/gruns/furl.'),
    packages=find_packages(),
    include_package_data=True,
    platforms=['any'],
    classifiers=[
        'License :: Public Domain',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    tests_require=[
        'flake8',
        'six>=1.8.0',
    ],
    install_requires=[
        'six>=1.8.0',
        'orderedmultidict>=1.0.1',
    ],
    cmdclass={
        'test': RunTests,
        'publish': Publish,
    },
)
