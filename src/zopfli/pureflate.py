'''
Some Deflate algorithms in pure Python

Can be used to manipulate Deflate blocks as objects etc.
'''
excodes = {257: (0, 3), 258: (0, 4), 259: (0, 5), 260: (0, 6), 261: (0, 7),
           262: (0, 8), 263: (0, 9), 264: (0, 10), 265: (1, 11), 266: (1, 13),
           267: (1, 15), 268: (1, 17), 269: (2, 19), 270: (2, 23),
           271: (2, 27), 272: (2, 31), 273: (3, 35), 274: (3, 43),
           275: (3, 51), 276: (3, 59), 277: (4, 67), 278: (4, 83),
           279: (4, 99), 280: (4, 115), 281: (5, 131), 282: (5, 163),
           283: (5, 195), 284: (5, 227), 285: (0, 258)}


exbits = {0: (0, 1), 1: (0, 2), 2: (0, 3), 3: (0, 4), 4: (1, 5), 5: (1, 7),
          6: (2, 9), 7: (2, 13), 8: (3, 17), 9: (3, 25), 10: (4, 33),
          11: (4, 49), 12: (5, 65), 13: (5, 97), 14: (6, 129), 15: (6, 193),
          16: (7, 257), 17: (7, 385), 18: (8, 513), 19: (8, 769),
          20: (9, 1025), 21: (9, 1537), 22: (10, 2049), 23: (10, 3073),
          24: (11, 4097), 25: (11, 6145), 26: (12, 8193), 27: (12, 12289),
          28: (13, 16385), 29: (13, 24577)}

hlenord = (16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15)


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


class HuffTree(object):
    def __init__(self):
        self.__tree = {}
        self.__rtree = {}

    def get(self, key):
        return self.__tree.get(key)

    def encode(self, i):
        return self.__rtree.get(i)

    def bylenlist(self, lenlist, MAX_BITS=15):
        self.cla = lenlist
        # 3.2.2 step 2
        code = 0
        next_code = {}
        for bits in range(1, MAX_BITS + 1):
            code = (code + lenlist.count(bits - 1)) << 1
            next_code[bits] = code
        # 3.2.2 step 3
        for n, len_ in enumerate(lenlist):
            if len_:
                codeT = tuple(reversed(int2bitseq(next_code[len_], len_)))
                self.__tree[codeT] = n
                self.__rtree[n] = codeT
                next_code[len_] += 1


staticHT = HuffTree()
staticHT.bylenlist((8,) * 144 + (9,) * 112 + (7,) * 24 + (8,) * 8)
staticDiH = HuffTree()
staticDiH.bylenlist((5,) * 32)


class Block(object):
    def __init__(self):
        self.decoded = []
        self.endbit = None
        self.blocktyp = 0
        self.final = 0

    def encodehuff(self, huff):
        cla = bytearray(huff.cla)
        res = bytearray()
        li0 = None
        while cla:
            simpl = False
            li = cla.pop(0)
            nm = min(len(cla) + 1, 138)
            if li == 0:
                n0 = 1
                while n0 < nm and cla[n0 - 1] == 0:
                    n0 += 1

                if n0 >= 11:
                    res.extend(self.headhuff.encode(18))
                    res.extend(int2bitseq(n0 - 11, 7))
                    cla = cla[n0 - 1:]
                elif n0 >= 3:
                    res.extend(self.headhuff.encode(17))
                    res.extend(int2bitseq(n0 - 3, 3))
                    cla = cla[n0 - 1:]
                else:
                    simpl = True
            elif li == li0:
                n0 = 1
                nm = min(len(cla) + 1, 7)
                while n0 < nm and cla[n0 - 1] == li0:
                    n0 += 1
                if n0 >= 3:
                    res.extend(self.headhuff.encode(16))
                    res.extend(int2bitseq(n0 - 3, 2))
                    cla = cla[n0 - 1:]
                else:
                    simpl = True
            else:
                simpl = True

            if simpl:
                res.extend(self.headhuff.encode(li))
            li0 = li

        return res

    def bitcode_item(self, item):
        res = bytearray()
        if isinstance(item, tuple):
            (le, dist) = item
            for i in excodes.iterkeys():
                if (i == 285 and le == 258) or \
                        (le >= excodes[i][1] and le < excodes[i + 1][1]):
                    res.extend(self.huff.encode(i))
                    res.extend(int2bitseq(le - excodes[i][1], excodes[i][0]))
            for i in exbits.iterkeys():
                if (i == 29 and dist >= 24577) or \
                        (dist >= exbits[i][1] and dist < exbits[i + 1][1]):
                    res.extend(self.dihuff.encode(i))
                    res.extend(int2bitseq(dist - exbits[i][1], exbits[i][0]))

        else:
            res.extend(self.huff.encode(item))
        return res

    def encodedbits(self):
        if self.blocktyp == 0:
            raise AssertionError("Can't bit encode uncompressed block")
        res = bytearray((self.final, ))
        res.extend(int2bitseq(self.blocktyp, 2))
        if self.blocktyp == 2:
            res.extend(int2bitseq(self.HLIT - 257, 5))
            res.extend(int2bitseq(self.HDIST - 1, 5))
            res.extend(int2bitseq(self.HLEN - 4, 4))
            for hle in hlenord[:self.HLEN]:
                res.extend(int2bitseq(self.clcla[hle], 3))
            res.extend(self.encodehuff(self.huff))
            res.extend(self.encodehuff(self.dihuff))
        for it in self.decoded:
            res.extend(self.bitcode_item(it))
        return res

    def encodedbytes(self, prev=None, encodelast=True):
        res = bytearray()
        if prev:
            z = bytearray(prev)
        else:
            z = bytearray()
        if self.blocktyp == 0:
            z.extend([self.final, 0, 0])
            tgtlen = 8 if len(z) <= 8 else 16
            addlen = tgtlen - len(z)
            z.extend((0,) * addlen)
            res.append(bitseq2int(z[:8]))
            if tgtlen == 16:
                res.append(bitseq2int(z[8:]))
            lbits = int2bitseq(len(self.decoded), 16)
            res.append(bitseq2int(lbits[:8]))
            res.append(bitseq2int(lbits[8:]))
            nlbits = int2bitseq(65535 - len(self.decoded), 16)
            res.append(bitseq2int(nlbits[:8]))
            res.append(bitseq2int(nlbits[8:]))
            res.extend(self.decoded)
            prev = None
        else:
            z.extend(self.encodedbits())
            k = len(z) // 8
            for i in range(0, k):
                it = z[i * 8:i * 8 + 8]
                res.append(bitseq2int(it))
            it = z[k * 8:k * 8 + 8]
            if encodelast and it:
                res.append(bitseq2int(it))
                prev = len(it)  # second result is bp for encodelast
        return (res, prev)

    def decode(self, data='', pre_work=bytearray()):
        '''Decode block from input data
        return rest of data in pair (data, tail) or None if incomplete block
        '''
        self.encoded = [bitseq2int(pre_work)] if pre_work else []
        self.startbit = (8 - len(pre_work) if pre_work else 0)
        self.work = pre_work
        self.buf = bytearray(data)
        try:
            self.final = self.pullbits(1)[0]
            self.blocktyp = bitseq2int(self.pullbits(2))
        except IndexError:
            # Incomplete stream
            return None
        if self.blocktyp == 3:
            raise AssertionError
        elif self.blocktyp == 0:
            # Not compressed
            self.work = []
            if len(self.buf) < 4:
                return None
            else:
                len_ = self.buf.pop(0)
                len_ = len_ * 256 + self.buf.pop(0)
                nlen = self.buf.pop(0)
                nlen = nlen * 256 + self.buf.pop(0)
                # TODO: check against len
            if len(self.buf) < len_:
                return None
            else:
                self.decoded.extend(self.buf[:len_])
                self.decoded.append(256)
                self.buf = self.buf[len_:]
        else:
            try:
                if self.blocktyp == 1:
                    self.huff = staticHT
                    self.dihuff = staticDiH
                else:
                    self.HLIT = bitseq2int(self.pullbits(5)) + 257
                    self.HDIST = bitseq2int(self.pullbits(5)) + 1
                    self.HLEN = bitseq2int(self.pullbits(4)) + 4
                    self.clcla = list((0,) * 19)
                    for hle in hlenord[:self.HLEN]:
                        self.clcla[hle] = bitseq2int(self.pullbits(3))
                    self.headhuff = HuffTree()
                    self.headhuff.bylenlist(self.clcla)
                    self.huff = self.buildhuff(self.headhuff, self.HLIT)
                    self.dihuff = self.buildhuff(self.headhuff, self.HDIST)
                self.decodeall()
            except IndexError:
                return None
        return (self.buf, self.work)

    def bitsize(self):
        return self.encoded * 8 - self.startbit + self.endbit - 8

    def pullbits(self, n=1):
        while len(self.work) < n:
            ch = self.buf.pop(0)
            self.encoded.append(ch)
            more = int2bitseq(ch, 8)
            self.work.extend(more)
        if n == 1:
            return (self.work.pop(0),)
        else:
            res = self.work[:n]
            self.work = self.work[n:]
            return res

    def readhuff(self, huff=None):
        if huff is None:
            huff = self.huff
        decoded = None
        pulled = []
        while decoded is None:
            pulled.append(self.pullbits()[0])
            decoded = huff.get(tuple(pulled))
        return decoded

    def buildhuff(self, headhuff, hlen):
        leni = 0
        cla = []
        while len(cla) < hlen:
            li = self.readhuff(headhuff)
            if li <= 15:
                leni = li
                cla.append(li)
            elif li == 16:
                n = 3 + bitseq2int(self.pullbits(2))
                cla.extend((leni,) * n)
            elif li == 17:
                n = 3 + bitseq2int(self.pullbits(3))
                cla.extend((0,) * n)
            elif li == 18:
                n = 11 + bitseq2int(self.pullbits(7))
                cla.extend((0,) * n)
        res = HuffTree()
        res.bylenlist(cla)
        return res

    def decodeone(self):
        decoded = self.readhuff()
        if decoded > 256:
            (extra, length) = excodes[decoded]
            if extra > 0:
                length += bitseq2int(self.pullbits(extra))
            dist = self.readhuff(self.dihuff)
            (extra, dist) = exbits[dist]
            if extra > 0:
                dist += bitseq2int(self.pullbits(extra))
            decoded = (length, dist)
        self.decoded.append(decoded)
        return decoded

    def decodeall(self):
        if not self.decoded:
            decoded = 0
            while decoded != 256:
                decoded = self.decodeone()
        return self.decoded
