#!/usr/bin/env python
from setuptools import setup
import sys

if sys.version_info < (3, 4):
    extra_requires = ['singledispatch>=3.4']
else:
    # functools.singledispatch is in stdlib from Python 3.4 onwards.
    extra_requires = []

setup(name='fluent.bundle',
      version='0.1',
      description='Localization library for expressive translations.',
      author='Mozilla',
      author_email='l10n-drivers@mozilla.org',
      license='APL 2',
      url='https://github.com/projectfluent/python-fluent',
      keywords=['fluent', 'localization', 'l10n'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
      ],
      packages=['fluent', 'fluent.bundle'],
      install_requires=['fluent>=0.9,<0.10'] + extra_requires,
      tests_require=['six'],
      test_suite='tests'
      )
