"""Minimal TIM2 reader/writer (4bpp/8bpp indexed, 32-bit CLUT; optional swizzle detection by caller).
python tools/tm2.py dump in.tm2 out.png [pal]"""
import struct, sys


class Pic:
    pass


def parse(d):
    assert d[:4] == b'TIM2'
    n, = struct.unpack_from('<H', d, 6)
    o = 16; pics = []
    for _ in range(n):
        p = Pic()
        p.off = o
        (p.total, p.clutsize, p.imgsize, p.hdrsize, p.clutcolors, p.fmt, p.mip, p.cluttype, p.imgtype,
         p.w, p.h) = struct.unpack_from('<IIIHHBBBBHH', d, o)
        p.gs = d[o + 24:o + 48]
        p.imgoff = o + p.hdrsize
        p.clutoff = p.imgoff + p.imgsize
        p.img = d[p.imgoff:p.imgoff + p.imgsize]
        p.clut = d[p.clutoff:p.clutoff + p.clutsize]
        pics.append(p)
        o += p.total
    return pics


def palette(p, idx=0):
    ncol = 16 if p.imgtype == 4 else 256
    cols = []
    base = idx * ncol * 4
    for i in range(ncol):
        r, g, b, a = p.clut[base + 4 * i:base + 4 * i + 4]
        cols.append((r, g, b, min(255, a * 2)))
    if p.imgtype == 5 and not (p.cluttype & 0x80):
        # CSM1 swizzle of 8-bit palettes
        c2 = cols[:]
        for i in range(256):
            j = (i & 0xe7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)
            c2[i] = cols[j]
        cols = c2
    return cols


def indices(p):
    if p.imgtype == 4:
        out = bytearray()
        for b in p.img: out += bytes([b & 15, b >> 4])
        return out
    return bytearray(p.img)


def to_png(p, path, pal=0):
    from PIL import Image
    cols = palette(p, pal)
    idx = indices(p)
    im = Image.new('RGBA', (p.w, p.h))
    im.putdata([cols[i] for i in idx[:p.w * p.h]])
    im.save(path)
    return im


if __name__ == '__main__':
    if sys.argv[1] == 'dump':
        d = open(sys.argv[2], 'rb').read()
        ps = parse(d)
        for p in ps:
            print(p.w, p.h, 'type', p.imgtype, 'clut', p.cluttype, p.clutcolors, 'fmt', p.fmt, 'mip', p.mip)
        to_png(ps[0], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 0)
