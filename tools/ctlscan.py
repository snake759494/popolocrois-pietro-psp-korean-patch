import json, struct, collections, sys
R = 'work/iso/PSP_GAME/USRDIR/data/'
files = json.load(open('work/blocks.json'))
ctl = collections.defaultdict(collections.Counter)
ex = {}
for f, bl in files.items():
    d = open(R + f, 'rb').read()
    for p, n, sig in bl:
        p = int(p, 16)
        t, = struct.unpack_from('<I', d, p + 0x3c)
        for i in range(n):
            idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
            s = d[p + off:p + off + ln + 1]
            j = 0
            while j < len(s):
                b = s[j]
                if 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc:
                    j += 2; continue
                if b < 0x20:
                    k = (sig, b)
                    ctl[k][s[j + 1:j + 2].hex()] += 1
                    ex.setdefault((sig, b, s[j + 1:j + 2].hex()), (f, s))
                j += 1
for k in sorted(ctl):
    print(k, dict(ctl[k].most_common(12)))
