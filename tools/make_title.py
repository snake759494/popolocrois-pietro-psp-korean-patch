"""Korean title logo for gui/pspo_logo.tm2 (512x92, 8bpp, alpha). Keeps 'POPOLOCROIS' and 'TM'."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tm2
from make_logo import styled_text, HEAVY, XB, ROOT

SRC = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/gui/pspo_logo.tm2')
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/gui/pspo_logo.tm2')


def write_tm2_rgba(d, p, im):
    q = im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    pal = q.getpalette(rawmode='RGBA')[:1024]
    pal += [0] * (1024 - len(pal))
    cols = [(pal[4 * i], pal[4 * i + 1], pal[4 * i + 2], (pal[4 * i + 3] + 1) // 2) for i in range(256)]
    stored = [None] * 256
    for i in range(256):
        j = (i & 0xe7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)
        stored[j] = cols[i]
    idx = bytes(q.getdata())
    d[p.imgoff:p.imgoff + p.imgsize] = idx
    d[p.clutoff:p.clutoff + p.clutsize] = b''.join(bytes(c) for c in stored)


def main():
    d = bytearray(open(SRC, 'rb').read())
    p = tm2.parse(bytes(d))[0]
    im = tm2.to_png(p, os.path.join(ROOT, 'work/tmp/pspo_orig.png')).convert('RGBA')
    clear = Image.new('RGBA', (512, 92), (0, 0, 0, 0))
    keep = im.crop((0, 0, 130, 15))          # POPOLOCROIS
    tm = im.crop((409, 74, 430, 92))         # TM mark
    im = clear.copy()
    im.paste(keep, (0, 0))
    f1 = ImageFont.truetype(HEAVY, 42)
    t1 = styled_text('포포로크로이스 이야기', f1, (40, 150, 40), (240, 230, 30),
                     (20, 70, 20, 255), 2, (255, 255, 255, 255), 2, track=-1)
    if t1.width > 400:
        t1 = t1.resize((400, int(t1.height * 400 / t1.width)), Image.LANCZOS)
    sh = Image.new('RGBA', t1.size, (0, 0, 0, 0))
    sh.putalpha(t1.split()[3].point(lambda v: int(v * 0.45)))
    im.alpha_composite(sh, (6, 15)); im.alpha_composite(t1, (4, 13))
    f2 = ImageFont.truetype(XB, 21)
    t2 = styled_text('피에트로 왕자의 모험', f2, (30, 110, 200), (10, 70, 150),
                     (255, 255, 255, 255), 2, (40, 80, 130, 255), 1)
    y2 = min(92 - t2.height, 13 + t1.height - 6)
    im.alpha_composite(t2, (404 - t2.width, y2))
    im.alpha_composite(tm, (410, 74))
    im.save(os.path.join(ROOT, 'work/tmp/pspo_ko.png'))
    write_tm2_rgba(d, p, im)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(d)
    tm2.to_png(tm2.parse(bytes(d))[0], os.path.join(ROOT, 'work/tmp/pspo_check.png'))


if __name__ == '__main__':
    main()
