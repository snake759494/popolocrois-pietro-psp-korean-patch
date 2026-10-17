"""Scan every file of the Korean ISO for leftover Japanese (kana runs in SJIS).
Kana codes are never produced by the Korean encoder, so any kana run is untranslated text.
usage: python tools/audit_kana.py [iso] -> work/audit.json"""
import os, re, sys, json, collections
import pycdlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ISO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Korean).iso')
KANA = rb'(?:\x82[\x9f-\xf1]|\x83[\x40-\x96]|\x81[\x5b\x45\x42\x41\x48\x49])'
pat = re.compile(rb'(?:' + KANA + rb'){3,}')
iso = pycdlib.PyCdlib(); iso.open(ISO)
res = collections.OrderedDict()
import io
for dp, _, fs in iso.walk(iso_path='/'):
    for f in fs:
        p = dp.rstrip('/') + '/' + f
        if p.lower().endswith(('.pmf', '.at3', '.png', '.sgb', '.xwb', '.prx')): continue
        b = io.BytesIO(); iso.get_file_from_iso_fp(b, iso_path=p); d = b.getvalue()
        hits = []
        for m in pat.finditer(d):
            s = m.group()
            if sum(1 for i in range(0, len(s), 2) if s[i] == 0x82 or s[i] == 0x83) < 3: continue
            hits.append((m.start(), s.decode('cp932', 'replace')))
        if hits:
            res[p.split(';')[0]] = hits
iso.close()
json.dump(res, open(os.path.join(ROOT, 'work/audit.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
tot = 0
for k, v in res.items():
    tot += len(v)
    print(len(v), k, v[0][1][:20])
print('files', len(res), 'hits', tot)
