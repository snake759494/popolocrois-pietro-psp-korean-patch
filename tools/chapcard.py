"""Chapter title cards (512x272 8bpp images embedded in event files at 0x770).
layout: 0x370 palette 256*RGBA, 0x770 header (fmt, w, h), 0x780 pixels."""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
EVT = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/evt')
CARDS = ['p0/1/121', 'p0/2/20d', 'p0/3/308', 'p0/4/402', 'p1/0/014', 'p1/1/100', 'p1/2/200',
         'p2/1/100', 'p2/2/200', 'p2/4/400', 'p2/5/500', 'p2/5/543']
PAL, HDR, PIX = 0x370, 0x770, 0x780
W, H = 512, 272


def load(name):
    d = open(os.path.join(EVT, name + '.p01'), 'rb').read()
    pal = np.frombuffer(d[PAL:PAL + 1024], np.uint8).reshape(256, 4)
    ix = np.frombuffer(d[PIX:PIX + W * H], np.uint8).reshape(H, W)
    return d, pal, ix


def rgb(pal, ix):
    return pal[ix][..., :3]


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'work/tmp'), exist_ok=True)
    o = Image.new('RGB', (W * 2, H * 6))
    for k, n in enumerate(CARDS):
        d, pal, ix = load(n)
        im = Image.fromarray(rgb(pal, ix))
        im.save(os.path.join(ROOT, 'work/tmp/card_%02d.png' % k))
        o.paste(im, ((k % 2) * W, (k // 2) * H))
    o.resize((W, H * 3)).save(os.path.join(ROOT, 'work/tmp/cards.png'))
