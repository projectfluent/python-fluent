#!/usr/bin/env python

from setuptools import setup

setup(name='fluent',
      version='0.3',
      description='Python fluent library',
      author='Staś Małolepszy',
      author_email='stas@mozilla.com',
      license='APL 2',
      url='https://github.com/projectfluent/python-fluent',
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
      ],
      packages=['fluent', 'fluent.syntax'],
      install_requires=[
          'six'
      ]
      )
