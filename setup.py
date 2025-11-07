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


def bool_from_environ(key: str, default: bool = False):
    """Get a boolean value from an environment variable."""
    value = os.environ.get(key)
    if not value:
        return default
    return value.lower() not in ("0", "false", "no", "off")


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

# Python Limited API for stable ABI support is enabled by default.
# Set USE_PY_LIMITED_API=0 to turn it off.
# https://docs.python.org/3/c-api/stable.html#limited-c-api
use_py_limited_api = bool_from_environ("USE_PY_LIMITED_API", default=True)
# NOTE: this must be kept in sync with python_requires='>=3.10' below
limited_api_min_version = "0x030a0000"  # Python 3.10

prefer_system_zopfli = bool(os.environ.get("USE_SYSTEM_ZOPFLI"))

# Build list of define_macros
define_macros = []
if use_py_limited_api:
    define_macros.append(("Py_LIMITED_API", limited_api_min_version))

if prefer_system_zopfli:
    system_define_macros = [("SYSTEM_ZOPFLI", "1")] + define_macros
    zopfli_ext_kwargs = {
        "sources": [
            "src/zopflimodule.c",
        ],
        "libraries": ["zopfli", "zopflipng"],
        "define_macros": system_define_macros,
    }
else:
    zopfli_ext_kwargs = {
        "sources": [
            "zopfli/src/zopfli/blocksplitter.c",
            "zopfli/src/zopfli/cache.c",
            "zopfli/src/zopfli/deflate.c",
            "zopfli/src/zopfli/gzip_container.c",
            "zopfli/src/zopfli/squeeze.c",
            "zopfli/src/zopfli/hash.c",
            "zopfli/src/zopfli/katajainen.c",
            "zopfli/src/zopfli/lz77.c",
            "zopfli/src/zopfli/tree.c",
            "zopfli/src/zopfli/util.c",
            "zopfli/src/zopfli/zlib_container.c",
            "zopfli/src/zopfli/zopfli_lib.c",
            "zopfli/src/zopflipng/lodepng/lodepng.cpp",
            "zopfli/src/zopflipng/lodepng/lodepng_util.cpp",
            "zopfli/src/zopflipng/zopflipng_lib.cc",
            "src/zopflimodule.c",
        ],
        "define_macros": define_macros,
    }

setup(
    name="zopfli",
    use_scm_version={"write_to": "src/zopfli/_version.py"},
    author="Adam DePrince",
    author_email="deprince@googlealumni.com",
    maintainer="Cosimo Lupo",
    maintainer_email="cosimo@anthrotype.com",
    description="Zopfli module for python",
    long_description=long_description,
    ext_modules=[
        Extension(
            "zopfli.zopfli", py_limited_api=use_py_limited_api, **zopfli_ext_kwargs
        )
    ],
    options={"bdist_wheel": {"py_limited_api": "cp310"}} if use_py_limited_api else {},
    package_dir={"": "src"},
    packages=["zopfli"],
    zip_safe=True,
    license="Apache-2.0",
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: System :: Archiving :: Compression",
    ],
    url="https://github.com/fonttools/py-zopfli",
    test_suite="tests",
    cmdclass={
        "build_ext": custom_build_ext,
    },
    setup_requires=["setuptools_scm"],
    extras_require={"test": ["pytest"]},
    python_requires=">=3.10",
)
