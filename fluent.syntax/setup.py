from setuptools import setup, find_namespace_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.rst'), 'rb') as f:
    long_description = f.read().decode('utf-8')

setup(name='fluent.syntax',
      description='Localization library for expressive translations.',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      author='Mozilla',
      author_email='l10n-drivers@mozilla.org',
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
      packages=find_namespace_packages(include=['fluent.*']),
      test_suite='tests.syntax'
      )
