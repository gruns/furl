import sys
from setuptools import setup, find_packages

import __info__ as pkginfo

if sys.argv[-1] == 'publish':
  os.system('python setup.py sdist upload')
  sys.exit()

long_description = ('''furl: URL parsing and manipulation made simple.

Information and documentation at: https://github.com/gruns/furl''')

setup(name=pkginfo.__title__,
      version=pkginfo.__version__,
      author=pkginfo.__author__,
      author_email=pkginfo.__contact__,
      url=pkginfo.__url__,
      packages=find_packages(),
      license=pkginfo.__license__,
      include_package_data=True,
      description='URL manipulation made simple.',
      long_description=long_description,
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
