#!/usr/bin/env python
"""
pyzopfli
======

Python bindings to zopfli
"""

from setuptools import setup, Extension

setup(
    name='zopfli',
    version='0.0.4',
    author='Adam DePrince',
    author_email='deprince@googlealumni.com',
    description='Zopfli module for python',
    long_description=__doc__,
    py_modules = [
        'zopfli',
        'zopfli.gzip',
        'zopfli.zlib',
        ],
    ext_modules = [Extension('zopfli.zopfli',
                             opts = "-O2 -W -Wall -Wextra -ansi -pedantic -lm",
                             sources = [
                                 'zopfli/blocksplitter.c',
                                 'zopfli/cache.c',
                                 'zopfli/deflate.c',
                                 'zopfli/gzip_container.c',
                                 'zopfli/squeeze.c',
                                 'zopfli/hash.c',
                                 'zopfli/katajainen.c',
                                 'zopfli/lz77.c', 
                                 'zopfli/tree.c',
                                 'zopfli/util.c',
                                 'zopfli/zlib_container.c',
                                 'zopfli/zopflimodule.c',
                ],
                             libraries = ['c']
                             )],
    packages = ["zopfli"],
    zip_safe=True,
    license='ASL',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: System :: Archiving :: Compression',
        ],
    scripts = [
        ],
    url = "https://github.com/obp/pyzopfli",
    install_requires = [
        ]
)

