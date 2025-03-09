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
with open(pjoin('furl', '__version__.py'), encoding='utf-8') as f:
    exec(f.read(), meta)


readmePath = pjoin(dirname(__file__), 'README.md')
with open(readmePath, encoding='utf-8') as f:
    readmeContent = f.read()


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

    To test all supported Python versions (as specified in tox.ini) in
    parallel, run

      $ tox -p

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
    long_description=readmeContent,
    long_description_content_type='text/markdown',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
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
