from __future__ import absolute_import

import zopfli.zopfli
from struct import pack
from zlib import adler32
from zlib import error
# This is mostly for compatibility reasons
from zlib import crc32
from zlib import decompress, decompressobj
ZLIB_RUNTIME_VERSION = '1.2.8'  # Mimic old version to guarantee no extra hopes
ZLIB_VERSION = '1.2.8'  # Mimic old version to guarantee no extra hopes
try:
    from zlib import Z_NO_FLUSH, Z_SYNC_FLUSH, Z_FULL_FLUSH, Z_FINISH
    from zlib import Z_NO_COMPRESSION, Z_BEST_SPEED, Z_BEST_COMPRESSION
    from zlib import Z_DEFAULT_COMPRESSION
    from zlib import DEFLATED, DEF_MEM_LEVEL, MAX_WBITS, DEF_BUF_SIZE
    from zlib import Z_DEFAULT_STRATEGY
    from zlib import Z_FILTERED, Z_HUFFMAN_ONLY, Z_RLE, Z_FIXED
except ImportError:
    # We can't work without original zlib in fact,
    # but these constants mentioned there to describe their usage

    # Flush modes
    Z_NO_FLUSH = 0
    # Z_PARTIAL_FLUSH = 1
    Z_SYNC_FLUSH = 2
    Z_FULL_FLUSH = 3
    Z_FINISH = 4
    # Z_BLOCK = 5
    # Z_TREES = 6
    # Compression levels.
    Z_NO_COMPRESSION = 0  # no use for now
    Z_BEST_SPEED = 1
    Z_BEST_COMPRESSION = 9
    Z_DEFAULT_COMPRESSION = -1
    # The deflate compression method (the only one supported in this version).
    DEFLATED = 8
    DEF_MEM_LEVEL = 8
    DEF_BUF_SIZE = 16384
    MAX_WBITS = 15
    # Compression strategy
    # Not used...
    Z_FILTERED = 1
    Z_HUFFMAN_ONLY = 2
    Z_RLE = 3
    Z_FIXED = 4
    Z_DEFAULT_STRATEGY = 0

levit = {-1: 15,
         0: 1,
         1: 1,
         2: 3,
         3: 5,
         4: 10,
         5: 15,
         6: 20,
         7: 30,
         8: 50,
         9: 100
         }
MASTER_BLOCK_SIZE = 20000000


def int2bitseq(data, length):
    res = []  # bytearray()
    nowbyte = data
    for _ in range(length):
        (nowbyte, bit) = divmod(nowbyte, 2)
        res.append(bit)
    return res


def bitseq2int(data):
    res = 0
    for bit in reversed(data):
        res = bit + res * 2
    return res


class compressobj(object):
    def __init__(self, level=Z_DEFAULT_COMPRESSION, method=DEFLATED,
                 wbits=MAX_WBITS, memlevel=DEF_MEM_LEVEL,
                 strategy=Z_DEFAULT_STRATEGY, **kwargs):
        '''simulate zlib deflateInit2
        level - compression level
        method - compression method, only DEFLATED supported
        wbits - should be in the range 8..15, practically ignored
                can also be -8..-15 for raw deflate
                zlib also have gz with "Add 16 to windowBit"
                                    - not implemented here
        memlevel - originally specifies how much memory should be allocated
                    zopfli - ignored
        strategy - originally is used to tune the compression algorithm
                    zopfli - ignored
        '''
        if method != DEFLATED:
            raise error
        self.raw = wbits < 0
        if abs(wbits) > MAX_WBITS or abs(wbits) < 5:
            raise ValueError
        self.crc = None
        self.buf = bytearray()
        self.prehist = bytearray()
        self.closed = False
        self.bit = 0
        self.first = True
        kwargs.pop('zdict', 0)  # not used
        kwargs.pop('memLevel', 0)  # not used
        self.opt = kwargs
        self.lastbyte = b''
        if 'numiterations' not in self.opt:
            if level in levit:
                self.opt['numiterations'] = levit[level]
            else:
                raise error

    def _header(self):
        cmf = 120
        flevel = 0
        fdict = 0
        cmfflg = 256 * cmf + fdict * 32 + flevel * 64
        fcheck = 31 - cmfflg % 31
        cmfflg += fcheck
        return pack('>H', cmfflg)

    def _updatecrc(self):
        if self.buf is None or self.raw:
            return
        if self.crc is None:
            self.crc = adler32(bytes(self.buf))
        else:
            self.crc = adler32(bytes(self.buf), self.crc)

    def _compress(self, final=None):
        self._updatecrc()
        blockfinal = 1 if final else 0
        indata = self.prehist
        prehist = len(self.prehist)
        indata.extend(self.buf)
        self.buf = bytearray()
        self.prehist = indata[-33000:]
        data = zopfli.zopfli.deflate(bytes(indata),
                                     old_tail=bytes(self.lastbyte),
                                     bitpointer=self.bit,
                                     blockfinal=blockfinal,
                                     prehist=prehist, **self.opt)
        res = bytearray(data[0])
        self.bit = data[1]

        if final:
            self.lastbyte = b''
            return res
        else:
            self.lastbyte = res[-32:]
            return res[:-32]

    def compress(self, string):
        global MASTER_BLOCK_SIZE
        self.buf.extend(bytearray(string))
        if len(self.buf) > MASTER_BLOCK_SIZE:
            out = bytearray()
            if not self.raw and self.first:
                out.extend(self._header())
                self.first = False
            out.extend(self._compress())
            return bytes(out)
        else:
            return b''

    def flush(self, mode=Z_FINISH):
        def encodedalign(prev):
            res = bytearray()
            z = bytearray(prev)
            # Not final, type 00
            z.extend([0, 0, 0])
            # if old tail + header cross byte border
            tgtlen = 8 if len(z) <= 8 else 16
            # Fit to bytes
            addlen = tgtlen - len(z)
            z.extend((0,) * addlen)
            # Add tail and header to result
            res.append(bitseq2int(z[:8]))
            if tgtlen == 16:
                res.append(bitseq2int(z[8:]))
            # zero length as we only want to align, no data
            res.extend(pack('>H', 0))  # LEN
            res.extend(pack('>H', 65535))  # NLEN
            return res

        if self.closed:
            raise error
        out = bytearray()
        self.closed = mode == Z_FINISH
        if not self.raw and self.first:
            out.extend(self._header())
            self.first = False
        if mode == Z_NO_FLUSH:
            return bytes(out)
        out.extend(self._compress(mode == Z_FINISH))
        if mode != Z_FINISH:
            self.bit = self.bit % 8
            # add void fixed block to align data to bytes
            if self.bit:
                work = int2bitseq(self.lastbyte.pop(), 8)[:self.bit]
            else:
                work = []
            self.lastbyte.extend(encodedalign(work))
            out.extend(self.lastbyte)
            self.lastbyte = b''
            self.bit = 0
            if mode == Z_FULL_FLUSH:
                self.prehist = bytearray()

        if not self.raw and mode == Z_FINISH:
            out.extend(pack('>L', self.crc))
        return bytes(out)


def compress(data, level=-1, **kwargs):
    """zlib.compress(data, **kwargs)

    """ + zopfli.__COMPRESSOR_DOCSTRING__ + """
    Returns:
      String containing a zlib container
    """
    if 'numiterations' not in kwargs:
        if level not in levit:
            raise error
        kwargs['numiterations'] = levit[level]

    kwargs['gzip_mode'] = 0
    return zopfli.zopfli.compress(bytes(data), **kwargs)
