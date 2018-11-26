#!/usr/bin/env python
import sys

from setuptools import setup

if sys.version_info < (3, 4):
    # functools.singledispatch is in stdlib from Python 3.4 onwards.
    extra_requires = ['singledispatch>=3.4']
else:
    extra_requires = []

setup(name='fluent',
      version='0.9.0',
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
      packages=['fluent', 'fluent.syntax'],
      install_requires=[
          'six>=1.10.0',
          'attrs>=18',
          'Babel>=2.5.3',
      ] + extra_requires,
      tests_require=['six'],
      test_suite='tests.syntax'
)
