#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='bbdb',
    version='0.0.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    dependencies=[
      'six==1.10.0',
      'sqlalchemy==1.1.12',
    ]
)
