"""BOOT.BIN SJIS strings with their references (data pointers and lui/addiu pairs)."""
import sys, os, struct, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elf import Elf

e = Elf()
d = e.d
v, o, fs, ms = e.segs[0]
# all 32-bit words that look like pointers into the image
words = collections.defaultdict(list)
for i in range(o, o + fs - 3, 4):
    w, = struct.unpack_from('<I', d, i)
    if v <= w < v + ms: words[w].append(i)
# lui/addiu pairs
code = collections.defaultdict(list)
regs = {}
for i in range(o, o + fs - 3, 4):
    w, = struct.unpack_from('<I', d, i)
    op = w >> 26
    if op == 0xf:
        regs[(w >> 16) & 31] = ((w & 0xffff) << 16, i)
    elif op in (9,) and ((w >> 21) & 31) in regs:
        hi, at = regs[(w >> 21) & 31]
        if i - at < 0x80:
            imm = w & 0xffff
            if imm >= 0x8000: imm -= 0x10000
            code[hi + imm].append(i)

pat = re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]|[\x20-\x7e\x0a])+\x00')
out = []
for m in pat.finditer(d):
    s = m.group()[:-1]
    if not any(b >= 0x81 for b in s): continue
    try: t = s.decode('cp932')
    except UnicodeDecodeError: continue
    va = e.o2v(m.start())
    if va is None: continue
    # also allow references to the string start only
    out.append({'off': m.start(), 'va': va, 'len': len(s), 'text': t,
                'dref': len(words.get(va, [])), 'cref': len(code.get(va, []))})
json.dump(out, open('work/boot_strings.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
c = collections.Counter((x['dref'] > 0, x['cref'] > 0) for x in out)
print(len(out), c)
