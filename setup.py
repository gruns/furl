#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# furl - URL manipulation made simple.
#
# Arthur Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: Build Amazing Things (Unlicense)

import os
import re
import sys
from os.path import dirname, join as pjoin
from setuptools import setup, find_packages

with open(pjoin(dirname(__file__), 'furl', '__init__.py')) as fd:
    VERSION = re.compile(
        r".*__version__ = '(.*?)'", re.S).match(fd.read()).group(1)

if sys.argv[-1] == 'publish':
    """Publish to PyPI with twine."""
    os.system('python setup.py sdist')
    os.system('twine upload dist/furl-%s.tar.gz' % VERSION)
    sys.exit()

long_description = (
    'Information and documentation at https://github.com/gruns/furl.')

tests_require = ['pycodestyle']
if sys.version_info[:2] < (2, 7):
    tests_require += ['unittest2']

setup(
    name='furl',
    version=VERSION,
    author='Arthur Grunseid',
    author_email='grunseid@gmail.com',
    url='https://github.com/gruns/furl',
    license='Unlicense',
    description='URL manipulation made simple.',
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    platforms=['any'],
    classifiers=[
        'Topic :: Software Development :: Libraries',
        'Natural Language :: English',
        'License :: Freely Distributable',
        'Intended Audience :: Developers',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=[
        'six>=1.8.0',
        'orderedmultidict>=0.7.8',
    ],
    test_suite='tests',
    tests_require=tests_require,
)
