#!/usr/bin/env python

import gzip
import zlib
from pathlib import Path
import zopfli.gzip
import zopfli.zlib
from io import BytesIO
import pytest


class BaseTests(object):
    data = (Path(__file__).parent.parent / "README.rst").read_bytes()

    def test_reversible(self):
        data = self.data
        assert self.decompress(self.compress(data)) == data

    def test_iterations_help(self):
        data = self.data
        assert len(self.compress(data, numiterations=1)) > len(
            self.compress(data, numiterations=1000)
        )


class TestZlib(BaseTests):
    compress = staticmethod(zopfli.zlib.compress)
    decompress = staticmethod(zlib.decompress)


class TestGzip(BaseTests):

    compress = staticmethod(zopfli.gzip.compress)

    def decompress(self, s):
        return gzip.GzipFile(fileobj=BytesIO(s)).read()


if __name__ == "__main__":
    import sys

    pytest.main(sys.argv)
