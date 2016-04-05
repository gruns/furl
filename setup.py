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
from sys import version_info
from os.path import dirname, join as pjoin
from setuptools import setup, find_packages

with open(pjoin(dirname(__file__), 'furl', '__init__.py')) as fd:
    VERSION = re.compile(
        r".*__version__ = '(.*?)'", re.S).match(fd.read()).group(1)

if sys.argv[-1] == 'publish':
    """Publish to PyPi."""
    os.system('python setup.py sdist upload')
    sys.exit()

long_description = (
    'Information and documentation at https://github.com/gruns/furl.')

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
        'Topic :: Internet',
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
        'orderedmultidict>=0.7.6',
    ],
    test_suite='tests',
    tests_require=[] if list(version_info[:2]) >= [2, 7] else ['unittest2'],
)
