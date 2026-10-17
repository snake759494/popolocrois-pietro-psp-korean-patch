import json, struct, collections
R = 'work/iso/PSP_GAME/USRDIR/data/'
files = json.load(open('work/blocks.json'))
uniq = collections.OrderedDict(); occ = 0
for f, bl in files.items():
    d = open(R + f, 'rb').read()
    for p, n, sig in bl:
        p = int(p, 16)
        t, = struct.unpack_from('<I', d, p + 0x3c)
        for i in range(n):
            idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
            s = d[p + off:p + off + ln]
            occ += 1
            uniq.setdefault(s, f)
tot = sum(len(s) for s in uniq)
print('occ', occ, 'unique', len(uniq), 'bytes', tot)
