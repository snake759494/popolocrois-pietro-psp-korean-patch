"""For every message block: is the string region [lowest offset, table) only strings + '$' padding?
Reports blocks whose region contains foreign bytes (data that repacking would clobber)."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgdb import R, ROOT

blocks = json.load(open(os.path.join(ROOT, 'work/blocks.json')))
bad = []
for f, bl in blocks.items():
    d = open(R + f, 'rb').read()
    for p, n, t in bl:
        ents = [struct.unpack_from('<HHI', d, p + t + 8 * i) for i in range(n)]
        lo = min(e[2] for e in ents)
        cover = bytearray(t - lo)
        for idx, ln, off in ents:
            for k in range(off - lo, off - lo + ln + 1):
                if 0 <= k < len(cover): cover[k] = 1
        foreign = [k for k in range(len(cover)) if not cover[k] and d[p + lo + k] != 0x24]
        if foreign:
            bad.append((f, p, n, t - lo, len(foreign), lo + foreign[0]))
print(len(bad), 'blocks with foreign bytes')
for b in bad[:40]: print(b)
json.dump(bad, open(os.path.join(ROOT, 'work/foreign.json'), 'w'))
