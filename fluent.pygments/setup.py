#!/usr/bin/env python
from setuptools import setup

setup(name='fluent.pygments',
      version='0.1.0',
      description='Pygments lexer for Fluent.',
      long_description='See https://github.com/projectfluent/python-fluent/ for more info.',
      author='Mozilla',
      author_email='l10n-drivers@mozilla.org',
      license='APL 2',
      url='https://github.com/projectfluent/python-fluent',
      keywords=['fluent', 'pygments'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
      ],
      packages=['fluent', 'fluent.pygments'],
      tests_require=['six'],
      test_suite='tests.pygments'
)
