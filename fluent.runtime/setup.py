#!/usr/bin/env python
from setuptools import setup
import sys

setup(name='fluent.runtime',
      version='0.1',
      description='Localization library for expressive translations.',
      long_description='See https://github.com/projectfluent/python-fluent/ for more info.',
      author='Luke Plant',
      author_email='L.Plant.98@cantab.net',
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
      packages=['fluent', 'fluent.runtime'],
      install_requires=[
          'fluent.syntax>=0.12,<=0.13',
          'attrs',
          'babel',
          'pytz',
      ],
      tests_require=['six'],
      test_suite='tests'
      )
