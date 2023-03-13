from os import path
from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), 'rb') as f:
    long_description = f.read().decode('utf-8')


setup(name='fluent.runtime',
      description='Localization library for expressive translations.',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Luke Plant',
      author_email='L.Plant.98@cantab.net',
      license='APL 2',
      url='https://github.com/projectfluent/python-fluent',
      keywords=['fluent', 'localization', 'l10n'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3 :: Only',
      ],
      packages=['fluent.runtime'],
      package_data={'fluent.runtime': ['py.typed']},
      # These should also be duplicated in tox.ini and /.github/workflows/fluent.runtime.yml
      install_requires=[
          'fluent.syntax>=0.17,<0.20',
          'attrs',
          'babel',
          'pytz',
          'typing-extensions>=3.7,<5'
      ],
      test_suite='tests',
      )
