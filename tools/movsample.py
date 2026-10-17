"""Decode the video of PMF files and save a contact sheet of frames every N seconds.
usage: python tools/movsample.py name [step_sec]"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import op_mux
from build_movies import decode, seconds

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MOV = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/mov')


def frames(name):
    pmf = open(os.path.join(MOV, name + '.pmf'), 'rb').read()
    es = op_mux.video_es(pmf) if hasattr(op_mux, 'video_es') else b''.join(pmf[o:o + n] for o, n in op_mux.slots(pmf))
    with tempfile.TemporaryDirectory() as t:
        return decode(es, t), seconds(pmf)


if __name__ == '__main__':
    name = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 3
    fr, sec = frames(name)
    fps = len(fr) / sec
    print(name, fr.shape, round(sec, 2), 'fps', round(fps, 2))
    idx = [int(i * step * fps) for i in range(int(sec / step) + 1) if int(i * step * fps) < len(fr)]
    tiles = [cv2.resize(fr[i], (240, 136)) for i in idx]
    for i, t in zip(idx, tiles):
        cv2.putText(t, '%.1f' % (i / fps), (3, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cols = 4
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(len(tiles) // cols)]
    os.makedirs(os.path.join(ROOT, 'work/tmp'), exist_ok=True)
    from PIL import Image; Image.fromarray(np.vstack(rows)[..., ::-1]).save(os.path.join(ROOT, 'work/tmp/mov_%s.png' % name))
