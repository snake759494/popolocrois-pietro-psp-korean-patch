"""Collect translatable SJIS strings of BOOT.BIN data area with their in-place byte budget.
budget = bytes from string start up to the next non-zero byte after its terminator (padding reuse), minus 1 for NUL.
writes work/boot_src.json [{off, budget, jp}]"""
import re, json, sys
d = open('work/iso/PSP_GAME/SYSDIR/BOOT.BIN', 'rb').read()
START = 0xdf000
pat = re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]|[\x20-\x7e\x0a])+\x00')
out = []
for m in pat.finditer(d, START):
    s = m.group()[:-1]
    st = m.start()
    # must start right after a NUL (or alignment) to be a real string start
    if d[st - 1] != 0: continue
    if not any(b >= 0x81 for b in s): continue
    try:
        t = s.decode('cp932')
    except UnicodeDecodeError:
        continue
    if not re.search('[぀-ヿ一-鿿！-～　-〿]', t): continue
    e = m.end()
    while e < len(d) and d[e] == 0: e += 1
    budget = e - st - 1
    out.append({'off': st, 'budget': budget, 'jp': t})
json.dump(out, open('work/boot_src.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), sum(len(x['jp']) for x in out))
