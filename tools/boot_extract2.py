"""Second pass over BOOT.BIN: SJIS strings missed by boot_extract.py because the byte before them
was not a NUL (float/format tails etc.), and NUL-terminated messages with control codes (0x0a, 0x1a).
writes work/boot_src2.json [{off, budget, jp}] (only strings not covered by boot_src.json)."""
import re, json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
d = open(os.path.join(ROOT, 'work/iso/PSP_GAME/SYSDIR/BOOT.BIN'), 'rb').read()
src = json.load(open(os.path.join(ROOT, 'work/boot_src.json'), encoding='utf-8'))
covered = set()
for x in src:
    covered.update(range(x['off'], x['off'] + x['budget'] + 1))
SJ = rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc])'
pat = re.compile(rb'(?:' + SJ + rb'|[\x0a]|[\x1a\x13])+\x00')
JP = re.compile('[぀-ヿ一-鿿]')
out = []
for m in pat.finditer(d, 0xdf000, 0xff900):
    st = m.start(); s = m.group()[:-1]
    if st in covered or any(k in covered for k in range(st, st + len(s))): continue
    if len(s) < 4: continue
    # must begin on a character boundary: walk back over a preceding SJIS pair is not allowed
    try:
        t = s.decode('cp932')
    except UnicodeDecodeError:
        continue
    if not JP.search(t): continue
    e = m.end()
    while e < len(d) and d[e] == 0: e += 1
    out.append({'off': st, 'budget': e - st - 1, 'jp': t})
json.dump(out, open(os.path.join(ROOT, 'work/boot_src2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for x in out: print(hex(x['off']), x['budget'], x['jp'][:40].replace('\n', '/'))
print(len(out))
