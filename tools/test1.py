import sys, os, json, shutil
sys.path.insert(0, 'tools')
from msgdb import R, entries
from msgpatch import repack
import kcode
from isobuild import Iso

ORIG = 'PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso'
OUT = 'work/test.iso'


def tok(s):
    """{xx} hex tokens + text"""
    import re
    out = b''
    for part in re.split(r'(\{[0-9a-f ]+\})', s):
        if not part: continue
        if part.startswith('{'):
            out += bytes.fromhex(part[1:-1])
        else:
            out += kcode.encode_text(part.replace('\\n', '\n')).replace(b'\xef\xbc\x8a', b'')
    return out


edits = {
    'evt/p0/1/100.p01': {0: '{17}피에트로{18}후우 다들 그렇게나 축하해 줬는데!{0a}{19 01}……{19 02} 왜 쓸쓸하지?{13}'},
    'evt/p3/0/004.p01': {},
}
iso = Iso(ORIG, OUT)
blocks = json.load(open('work/blocks.json'))
for f, ed in edits.items():
    d = bytearray(open(R + f, 'rb').read())
    for p, n, t in blocks[f]:
        es = entries(d, p)
        news = [bytes(s) for ln, off, s in es]
        for i, s in enumerate(news):
            pass
        for i, txt in ed.items():
            news[i] = tok(txt)
        print('repack', repack(d, p, news))
        break
    print(iso.replace('/PSP_GAME/USRDIR/data/' + f, bytes(d)))
for nm in ['kanji12.fnt', 'jk18_020.fnt', 'menu24.fnt']:
    print(nm, iso.replace('/PSP_GAME/USRDIR/data/fonts/' + nm, open('work/tmp/fonts/' + nm, 'rb').read()))
iso.close()
