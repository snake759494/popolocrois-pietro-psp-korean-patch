"""PoPoLoCrois rxFont (.fnt) reader/writer.
header (fmt = (b0 & 0xc) >> 2):
  fmt0/1: 8 bytes ; fmt2: 0x28 bytes ; fmt3: d[0x28] bytes (0x2a, includes font name)
  b2 = line height, b4..5 = glyph count (big endian)
records[count] * 20 bytes:
  0 bitmap w, 1 advance, 2 ascent, 3 descent (h = asc+desc), 4 x bearing (s8), 5 0, 6 code (u16 LE, informational)
  rect: fmt0/1: x0 = r8 (+r16<<8 fmt1), x1 = r18 (+wrap,+r16<<8 fmt1), y0 = r9 + u16(r14)<<8, y1 = r19 + u16(r14)<<8 (+wrap)
        fmt3:   x0 = r8|r12<<8, y0 = r9|r13<<8, x1 = r18|r16<<8, y1 = r19|r17<<8
codes[count] u16 (sorted, SJIS value), padded to 4
u16 h, u16 w, 4bpp texture (value 0 = empty, 1 = full ink ... 15 = faint)
"""
import struct


class Fnt:
    def __init__(self, path):
        d = self.d = open(path, 'rb').read()
        self.fmt = (d[0] & 0xc) >> 2
        hl = 8 if self.fmt < 2 else (0x28 if self.fmt == 2 else d[0x28])
        self.hdr = bytearray(d[:hl])
        self.n = struct.unpack_from('>H', d, 4)[0]
        self.recs = [bytearray(d[hl + 20 * i:hl + 20 + 20 * i]) for i in range(self.n)]
        o = hl + 20 * self.n
        self.codes = list(struct.unpack_from('<%dH' % self.n, d, o))
        o += 2 * self.n
        if self.n & 1: o += 2
        self.th, self.tw = struct.unpack_from('<HH', d, o)
        o += 4
        self.texoff = o
        self.tex = d[o:o + self.tw * self.th // 2].ljust(self.tw * self.th // 2, b'\0')
        self.tail = d[o + self.tw * self.th // 2:]

    def rect(self, r):
        if self.fmt >= 2:
            return r[8] | r[12] << 8, r[9] | r[13] << 8, r[18] | r[16] << 8, r[19] | r[17] << 8
        yh = struct.unpack_from('<H', r, 0xe)[0] << 8
        y0 = r[9] + yh; y1 = r[0x13] + yh
        x0 = r[8]; x1 = r[0x12]
        if self.fmt > 0:
            if x1 < x0: x1 += 0x100
            x0 += r[0x10] << 8; x1 += r[0x10] << 8
        if y1 < y0: y1 += 0x100
        return x0, y0, x1, y1

    def set_rect(self, r, x0, y0, x1, y1):
        for k in range(8, 20): r[k] = 0
        if self.fmt >= 2:
            r[8] = x0 & 0xff; r[12] = x0 >> 8; r[9] = y0 & 0xff; r[13] = y0 >> 8
            r[18] = x1 & 0xff; r[16] = x1 >> 8; r[19] = y1 & 0xff; r[17] = y1 >> 8
            r[14] = y0 >> 8
        else:
            yh = y0 >> 8
            assert (y1 - (yh << 8)) < 0x200
            r[9] = y0 & 0xff; r[19] = y1 & 0xff; r[13] = y0 & 0xff; r[17] = y1 & 0xff
            struct.pack_into('<H', r, 0xe, yh)
            if self.fmt == 1:
                xh = x0 >> 8
                r[8] = x0 & 0xff; r[18] = x1 & 0xff; r[12] = x1 & 0xff; r[16] = xh
                assert x1 - (xh << 8) < 0x200
            else:
                assert x1 < 256
                r[8] = x0; r[18] = x1; r[12] = x1; r[16] = x0
        assert self.rect(r) == (x0, y0, x1, y1), (self.rect(r), (x0, y0, x1, y1))

    def glyph(self, i):
        """return list of rows of nibble values"""
        x0, y0, x1, y1 = self.rect(self.recs[i])
        rows = []
        for y in range(y0, y1):
            row = []
            for x in range(x0, x1):
                b = self.tex[(y * self.tw + x) >> 1]
                row.append((b >> 4) if x & 1 else (b & 15))
            rows.append(row)
        return rows

    def image(self):
        from PIL import Image
        px = bytearray()
        for b in self.tex: px += bytes([(b & 15) * 17, (b >> 4) * 17])
        return Image.frombytes('L', (self.tw, self.th), bytes(px))

    def save(self, path):
        n = len(self.recs)
        assert n == len(self.codes) and self.codes == sorted(self.codes)
        h = bytearray(self.hdr)
        struct.pack_into('>H', h, 4, n)
        out = bytearray(h)
        for r in self.recs: out += r
        out += struct.pack('<%dH' % n, *self.codes)
        if n & 1: out += b'\0\0'
        out += struct.pack('<HH', self.th, self.tw)
        out += self.tex
        open(path, 'wb').write(out)
