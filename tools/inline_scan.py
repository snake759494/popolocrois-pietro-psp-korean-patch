"""Find script-inline strings (outside message blocks): NUL-terminated SJIS text using '\\n\\x0b' line
breaks, '$w' waits and '@' end marks. Writes work/inline.json [{file, off, len, jp}] (original data)."""
import os, re, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgdb import R, ROOT

blocks = json.load(open(os.path.join(ROOT, 'work/blocks.json')))
SJ = rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc])'
pat = re.compile(rb'(?:' + SJ + rb'|\n\x0b|\n|\$w|@|[\x20-\x3f\x41-\x7e])+\x00')
KANA = re.compile('[ぁ-ヶ]')
out = []
for dp, _, fs in os.walk(R):
    for fn in fs:
        if not fn.endswith(('.p00', '.p01', '.p10')): continue
        f = os.path.join(dp, fn).replace(os.sep, '/')[len(R):]
        d = open(R + f, 'rb').read()
        regs = []
        for p, n, t in blocks.get(f, []):
            regs.append((p, p + t + 8 * n))
        for m in pat.finditer(d):
            s = m.group()[:-1]
            st = m.start()
            # trim leading ASCII noise (opcode bytes)
            k = 0
            while k < len(s) and s[k] < 0x80: k += 1
            s2 = s[k:]; st2 = st + k
            if len(s2) < 6: continue
            if any(a <= st2 < b for a, b in regs): continue
            try:
                t = s2.decode('cp932')
            except UnicodeDecodeError:
                continue
            if len(KANA.findall(t)) < 2: continue
            if 'DebugMessage' in t or t.startswith(('P0', 's1_', 's2_', 's3_')): continue
            if b'\x0b' not in s2 and b'@' not in s2 and b'$w' not in s2: continue
            out.append({'file': f, 'off': st2, 'len': len(s2), 'jp': t, 'pre': d[st2 - 4:st2].hex()})
json.dump(out, open(os.path.join(ROOT, 'work/inline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), len(set(x['jp'] for x in out)))
for x in out[:20]: print(x['file'], hex(x['off']), x['len'], x['pre'], repr(x['jp'][:40]))
