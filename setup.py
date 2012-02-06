import os
import sys
from setuptools import setup, find_packages

if sys.argv[-1] == 'publish':
  os.system('python setup.py sdist upload')
  sys.exit()

long_description = ('''furl: URL parsing and manipulation made simple.

Information and documentation at: https://github.com/gruns/furl''')

setup(name='furl',
      version='0.3', # Keep synchronized with __init__.py.
      author='Arthur Grunseid',
      author_email='grunseid@gmail.com',
      url='https://github.com/gruns/furl',
      license='Unlicense',
      description='URL manipulation made simple.',
      long_description=long_description,
      packages=find_packages(),
      include_package_data=True,
      platforms=['any'],
      classifiers=['Topic :: Internet',
                   'Natural Language :: English',
                   'Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: Freely Distributable',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   ],
      install_requires=['orderedmultidict >= 0.7'],
      test_suite='tests',
      tests_require=[],
      )
