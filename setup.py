#!/usr/bin/env python
"""
pyzopfli
======

Python bindings to zopfli
"""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class custom_build_ext(build_ext):
    """Pass platform-specific compiler/linker flags"""

    def build_extensions(self):
        compiler_type = self.compiler.compiler_type
        if compiler_type == "msvc":
            for ext in self.extensions:
                ext.extra_compile_args.append("/Za")
        elif compiler_type in ("unix", "cygwin", "mingw32"):
            for ext in self.extensions:
                ext.extra_compile_args.extend([
                    "-ansi",
                    "-pedantic",
                    # python uses long long (C99), so we mute the warning
                    "-Wno-long-long",
                ])
                # on some Unix-like systems, such as Linux, the libc math
                # library is not linked by default
                ext.extra_link_args.append("-lm")
        build_ext.build_extensions(self)


setup(
    name='zopfli',
    version='0.1.0',
    author='Adam DePrince',
    author_email='deprince@googlealumni.com',
    description='Zopfli module for python',
    long_description=__doc__,
    ext_modules = [
        Extension('zopfli.zopfli',
            sources=[
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
                'src/zopflimodule.c',
            ],
        )
    ],
    package_dir={"": "src"},
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
    url = "https://github.com/obp/zopfli",
    test_suite="tests",
    cmdclass={
        "build_ext": custom_build_ext,
    },
)
