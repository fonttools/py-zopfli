#!/usr/bin/env python

import gzip
import unittest
import zlib
import zopfli.gzip
import zopfli.zlib
from io import BytesIO

class Tests(object):
    data = unittest.__doc__.encode('utf-8')
    def test_reversible(self):
        data = self.data 
        self.assertEqual(self.decompress(self.compress(data)), data)

    def test_iterations_help(self):
        data = self.data
        self.assertTrue(len(self.compress(data, numiterations=1)) > len(self.compress(data, numiterations=1000)))

class ZlibTest(unittest.TestCase, Tests):
    compress = staticmethod(zopfli.zlib.compress)
    decompress = staticmethod(zlib.decompress)

class GzipTest(unittest.TestCase, Tests):

    compress = staticmethod(zopfli.gzip.compress)
    
    def decompress(self, s):
        return gzip.GzipFile(fileobj=BytesIO(s)).read()
        

if __name__ == "__main__":
    unittest.main()
