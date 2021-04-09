from setuptools import setup, find_namespace_packages

setup(
    name='fluent.docs',
    packages=find_namespace_packages(include=['fluent.*']),
)
