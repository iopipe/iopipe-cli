#!/usr/bin/env python3
from setuptools import setup

setup(
    name='iopipe_install',
    version='0.1',
    py_modules=['iopipe-install'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        iopipe-install=iopipe_install:cli
    ''',
)
