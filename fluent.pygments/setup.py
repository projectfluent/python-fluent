#!/usr/bin/env python
from setuptools import setup
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.rst'), 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(name='fluent.pygments',
      description='Pygments lexer for Fluent.',
      long_description=long_description,
      long_description_content_type='text/x-rst',
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
