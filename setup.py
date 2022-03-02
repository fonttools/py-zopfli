#!/usr/bin/env python
"""
pyzopfli
======

Python bindings to zopfli
"""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from io import open
import os


class custom_build_ext(build_ext):
    """Pass platform-specific compiler/linker flags"""

    def build_extensions(self):
        compiler_type = self.compiler.compiler_type
        if compiler_type in "unix":
            for ext in self.extensions:
                # on some Unix-like systems, such as Linux, the libc math
                # library is not linked by default:
                # https://github.com/cython/cython/issues/1585
                ext.extra_link_args.append("-lm")
        build_ext.build_extensions(self)


with open("README.rst", "r", encoding="utf-8") as readme:
    long_description = readme.read()

prefer_system_zopfli = bool(os.environ.get('USE_SYSTEM_ZOPFLI'))
if prefer_system_zopfli:
    zopfli_ext_kwargs = {
        'sources': [
            'src/zopflimodule.c',
        ],
        'libraries': ['zopfli', 'zopflipng'],
        'define_macros': [('SYSTEM_ZOPFLI', '1')],
    }
else:
    zopfli_ext_kwargs = {
        'sources': [
            'zopfli/src/zopfli/blocksplitter.c',
            'zopfli/src/zopfli/cache.c',
            'zopfli/src/zopfli/deflate.c',
            'zopfli/src/zopfli/gzip_container.c',
            'zopfli/src/zopfli/squeeze.c',
            'zopfli/src/zopfli/hash.c',
            'zopfli/src/zopfli/katajainen.c',
            'zopfli/src/zopfli/lz77.c',
            'zopfli/src/zopfli/tree.c',
            'zopfli/src/zopfli/util.c',
            'zopfli/src/zopfli/zlib_container.c',
            'zopfli/src/zopfli/zopfli_lib.c',
            'zopfli/src/zopflipng/lodepng/lodepng.cpp',
            'zopfli/src/zopflipng/lodepng/lodepng_util.cpp',
            'zopfli/src/zopflipng/zopflipng_lib.cc',
            'src/zopflimodule.c',
        ],
    }

setup(
    name='zopfli',
    use_scm_version={"write_to": "src/zopfli/_version.py"},
    author='Adam DePrince',
    author_email='deprince@googlealumni.com',
    maintainer='Cosimo Lupo',
    maintainer_email='cosimo@anthrotype.com',
    description='Zopfli module for python',
    long_description=long_description,
    ext_modules=[
        Extension('zopfli.zopfli', **zopfli_ext_kwargs)
    ],
    package_dir={"": "src"},
    packages=["zopfli"],
    zip_safe=True,
    license='ASL',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: System :: Archiving :: Compression',
    ],
    url="https://github.com/fonttools/py-zopfli",
    test_suite="tests",
    cmdclass={
        "build_ext": custom_build_ext,
    },
    setup_requires=["setuptools_scm"],
    extras_require={"test": ["pytest"]},
    python_requires=">=3.7",
)
