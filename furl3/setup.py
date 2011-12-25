from setuptools import setup, find_packages

import furl

setup(name='furl',
      version=furl.__version__,
      author=furl.__author__,
      author_email='grunseid@gmail.com',
      url='https://github.com/gruns/furl',
      packages=find_packages(),
      license=furl.__license__,
      include_package_data=True,
      description='URL manipulation made simple.',
      long_description='URL parsing and manipulation made simple.',
      platforms=['any'],
      classifiers=['Topic :: Internet',
                   'Natural Language :: English',
                   'Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: Freely Distributable',
                   'Programming Language :: Python :: 3.2',
                   ],
      install_requires=[''],
      test_suite='tests',
      tests_require=[],
      )
