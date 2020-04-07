#!/usr/bin/env python
from setuptools import setup


setup(name='fluent.runtime',
      version='0.3',
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
      # These should also be duplicated in tox.ini and ../.travis.yml
      install_requires=[
          'fluent.syntax>=0.17,<0.18',
          'attrs',
          'babel',
          'pytz',
          'six',
      ],
      test_suite='tests',
      tests_require=[
          'mock',
      ],
      )
