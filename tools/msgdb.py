"""Message block access.
Block header: +0x00 u16 kind (0,1 = old fmt, end 0x13 ; 2,3 = new fmt, end 0x1a), +0x02 u16 (2 or 0)
+0x36 u16 id, +0x38 u16 count, +0x3c u32 table off, +0x40 u32 next, +0x44 u32 title
table entry: u16 idx, u16 len (incl. end code, excl. 00), u32 off (block-relative)
"""
import os, struct, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/')
SIGS = {b'\x01\x00\x02\x00', b'\x03\x00\x00\x00', b'\x00\x00\x02\x00', b'\x02\x00\x00\x00'}


def find_blocks(d):
    out = []
    for p in range(0, len(d) - 0x48, 16):
        if d[p:p + 4] not in SIGS: continue
        n, = struct.unpack_from('<H', d, p + 0x38)
        if not 0 < n < 4000: continue
        t, = struct.unpack_from('<I', d, p + 0x3c)
        if t < 0x48 or t & 3 or p + t + 8 * n > len(d): continue
        ok = True
        for i in range(n):
            idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
            if idx != i or off < 0x40 or off + ln > t or ln == 0:
                ok = False; break
        if ok:
            out.append((p, n, t))
    return out


def entries(d, p):
    n, = struct.unpack_from('<H', d, p + 0x38)
    t, = struct.unpack_from('<I', d, p + 0x3c)
    res = []
    for i in range(n):
        idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
        res.append((ln, off, d[p + off:p + off + ln]))
    return res


def all_files():
    for dp, _, fs in os.walk(R):
        for f in sorted(fs):
            if f.endswith(('.p00', '.p01', '.p10', '.p99')):
                yield os.path.join(dp, f).replace(os.sep, '/')[len(R):]


if __name__ == '__main__':
    import sys
    res = {}
    for f in all_files():
        d = open(R + f, 'rb').read()
        bl = find_blocks(d)
        if bl: res[f] = [[p, n, t] for p, n, t in bl]
    json.dump(res, open(os.path.join(ROOT, 'work/blocks.json'), 'w'))
    print(len(res), sum(n for v in res.values() for p, n, t in v))
