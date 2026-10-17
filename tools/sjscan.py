"""List NUL-terminated SJIS strings in a binary. usage: sjscan.py file [minchars]"""
import re, sys
d = open(sys.argv[1], 'rb').read()
mn = int(sys.argv[2]) if len(sys.argv) > 2 else 2
pat = re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|[\x0a])+\x00')
n = 0; tot = 0
for m in pat.finditer(d):
    s = m.group()[:-1]
    if sum(1 for b in s if b >= 0x81) < mn * 2: continue
    try:
        t = s.decode('cp932')
    except UnicodeDecodeError:
        continue
    n += 1; tot += len(t)
    print('%06x %s' % (m.start(), t.replace('\n', '\\n')))
print('#', n, tot, file=sys.stderr)
