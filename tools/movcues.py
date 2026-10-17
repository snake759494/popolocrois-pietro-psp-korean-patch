"""Find burned-in caption intervals of a PMF (bright, low-saturation text in a region).
usage: python tools/movcues.py name x0 y0 x1 y1 [thr]  -> prints intervals, saves sample crops"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import movsample

ROOT = movsample.ROOT


def textmask(f, thr=205):
    f = f.astype(np.int16)
    mx = f.max(2); mn = f.min(2)
    return (mn > thr) & (mx - mn < 40)


if __name__ == '__main__':
    name = sys.argv[1]
    x0, y0, x1, y1 = map(int, sys.argv[2:6])
    thr = int(sys.argv[6]) if len(sys.argv) > 6 else 205
    npy = os.path.join(ROOT, 'work/tmp/%s.npy' % name)
    if os.path.exists(npy): fr = np.load(npy)
    else:
        fr, _ = movsample.frames(name); np.save(npy, fr)
    fps = 29.97
    cnt = np.array([textmask(f[y0:y1, x0:x1], thr).sum() for f in fr])
    on = cnt > 60
    iv = []; s = None
    for i, v in enumerate(on):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s > 8: iv.append((s, i))
            s = None
    if s is not None: iv.append((s, len(on)))
    out = []
    for k, (a, b) in enumerate(iv):
        m = (a + b) // 2
        msk = textmask(fr[m][y0:y1, x0:x1], thr)
        ys, xs = np.where(msk)
        box = [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max()), int(y0 + ys.max())]
        out.append({'start': round(a / fps, 2), 'end': round(b / fps, 2), 'box': box, 'mid': m})
        Image.fromarray(fr[m][:, :, ::-1]).save(os.path.join(ROOT, 'work/tmp/cue_%s_%02d.png' % (name, k)))
        print(k, out[-1])
    json.dump(out, open(os.path.join(ROOT, 'work/tmp/cues_%s.json' % name), 'w'))
