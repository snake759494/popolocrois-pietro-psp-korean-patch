import json, sys, collections
sys.path.insert(0, 'tools')
from msgdb import R, entries
blocks = json.load(open('work/blocks.json'))


def show(s):
    o = ''; j = 0
    while j < len(s):
        b = s[j]
        if (0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc) and j + 1 < len(s):
            o += s[j:j + 2].decode('cp932', 'replace'); j += 2
        elif 0x20 <= b < 0x7f:
            o += chr(b); j += 1
        else:
            o += '{%02x}' % b; j += 1
    return o


ex = collections.defaultdict(list)
for f, bl in blocks.items():
    d = open(R + f, 'rb').read()
    for p, n, t in bl:
        kind = d[p]
        for ln, off, s in entries(d, p):
            j = 0
            while j < len(s):
                b = s[j]
                if 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc: j += 2; continue
                if b < 0x20 and b != 0x0a:
                    k = ('old' if kind < 2 else 'new', b)
                    if len(ex[k]) < int(sys.argv[1]): ex[k].append(f + ' ' + show(s))
                j += 1
for k in sorted(ex):
    print('=====', k)
    for e in ex[k]: print('   ', e)
