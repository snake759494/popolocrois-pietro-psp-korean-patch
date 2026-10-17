import os, re, sys, collections
R = 'work/iso/PSP_GAME'
pat = re.compile(rb'(?:[\x82\x83][\x40-\xfc]|\x81[\x40-\xac]|[\x88-\x9f\xe0-\xea][\x40-\xfc]){4,}')
tot = collections.Counter(); ex = {}
for dp, _, fs in os.walk(R):
    for f in fs:
        p = os.path.join(dp, f).replace(os.sep, '/'); d = open(p, 'rb').read()
        m = pat.findall(d)
        n = sum(len(x) for x in m)
        if n > 200:
            k = re.sub(r'/[^/]*$', '/*', p) + ' ' + p.rsplit('.', 1)[-1]
            tot[k] += n
            ex.setdefault(k, (p, m[:3]))
for k, v in sorted(tot.items(), key=lambda x: -x[1])[:70]:
    print(v, k, [x.decode('cp932', 'replace') for x in ex[k][1]])
