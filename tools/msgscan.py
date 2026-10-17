"""Find message blocks: header with count@0x38, table off@0x3c, table entries (u16 idx,u16 len,u32 off)."""
import os, struct, sys, collections, json
R = 'work/iso/PSP_GAME/USRDIR/data/'


def find_blocks(d):
    out = []
    for p in range(0, len(d) - 0x48, 16):
        n, = struct.unpack_from('<H', d, p + 0x38)
        if not 0 < n < 4000: continue
        t, = struct.unpack_from('<I', d, p + 0x3c)
        if t < 0x48 or t & 3 or p + t + 8 * n > len(d): continue
        ok = True
        for i in range(min(n, 3)):
            idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
            if idx != i or off < 0x40 or off + ln > t or ln == 0:
                ok = False; break
        if ok:
            out.append((p, n, t))
    return out


if __name__ == '__main__':
    stats = collections.Counter(); files = {}
    for dp, _, fs in os.walk(R):
        for f in fs:
            path = os.path.join(dp, f).replace(os.sep, '/')
            d = open(path, 'rb').read()
            bl = find_blocks(d)
            if bl:
                files[path[len(R):]] = [(hex(p), n, d[p:p + 4].hex()) for p, n, t in bl]
                k = path[len(R):].split('/')[0] + '/' + path.rsplit('.', 1)[-1]
                stats[k] += sum(n for p, n, t in bl)
    for k, v in stats.most_common(): print(k, v)
    json.dump(files, open('work/blocks.json', 'w'), indent=0)
    print(len(files))
