import os, sys, struct, glob, collections
R = 'work/iso/PSP_GAME/USRDIR/data/'
c = collections.Counter()
for p in sorted(glob.glob(R + sys.argv[1], recursive=True)):
    d = open(p, 'rb').read()
    a, b, n = struct.unpack_from('<III', d, 0)
    t = d[n:n + 16].hex() if n < len(d) else '-'
    c[(a, b, t[:8])] += 1
    if len(sys.argv) > 2: print(p[len(R):], len(d), a, b, hex(n), t)
for k, v in c.most_common(30): print(v, k)
