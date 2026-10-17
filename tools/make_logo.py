"""Korean title logo: replaces the Japanese lettering of gui/logo00.tm2 (keeps 'POPOLOCROIS').
writes work/gfx_out/USRDIR/data/gui/logo00.tm2 and a preview png."""
import os, sys, struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tm2

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/gui/logo00.tm2')
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/gui/logo00.tm2')
HEAVY = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')
XB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')


def styled_text(text, font, fill_top, fill_bot, inner, inner_w, outer, outer_w, track=0):
    # measure
    tmp = Image.new('L', (10, 10)); dr = ImageDraw.Draw(tmp)
    widths = [dr.textlength(c, font=font) for c in text]
    W = int(sum(widths) + track * (len(text) - 1)) + 2 * (inner_w + outer_w) + 8
    asc, desc = font.getmetrics()
    H = asc + desc + 2 * (inner_w + outer_w) + 8
    mask = Image.new('L', (W, H), 0)
    dm = ImageDraw.Draw(mask)
    x = inner_w + outer_w + 4
    for c, w in zip(text, widths):
        dm.text((x, inner_w + outer_w + 4), c, font=font, fill=255)
        x += w + track
    bb = mask.getbbox()
    def grow(m, r):
        return m.filter(ImageFilter.MaxFilter(2 * r + 1)) if r > 0 else m
    m_in = grow(mask, inner_w)
    m_out = grow(m_in, outer_w)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    img.paste(Image.new('RGBA', (W, H), outer), (0, 0), m_out)
    img.paste(Image.new('RGBA', (W, H), inner), (0, 0), m_in)
    grad = Image.new('RGBA', (W, H))
    top, bot = bb[1], bb[3]
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        t = min(1, max(0, (y - top) / max(1, bot - top)))
        col = tuple(int(fill_top[i] * (1 - t) + fill_bot[i] * t) for i in range(3)) + (255,)
        gd.line([(0, y), (W, y)], fill=col)
    img.paste(grad, (0, 0), mask)
    return img.crop(m_out.getbbox())


def main():
    d = bytearray(open(SRC, 'rb').read())
    p = tm2.parse(bytes(d))[0]
    base = tm2.to_png(p, os.path.join(ROOT, 'work/tmp/logo00_orig.png')).convert('RGBA')
    im = base.copy()
    # erase the Japanese lettering (title + subtitle), keep POPOLOCROIS (y < 52, x < 160)
    dr = ImageDraw.Draw(im)
    dr.rectangle([30, 52, 460, 126], fill=(255, 255, 255, 255))
    dr.rectangle([160, 30, 460, 52], fill=(255, 255, 255, 255))
    # main title
    f1 = ImageFont.truetype(HEAVY, 40)
    t1 = styled_text('포포로크로이스 이야기', f1, (40, 150, 40), (240, 230, 30),
                     (20, 70, 20, 255), 2, (255, 255, 255, 255), 2, track=-1)
    if t1.width > 410:
        t1 = t1.resize((410, int(t1.height * 410 / t1.width)), Image.LANCZOS)
    # drop shadow
    sh = Image.new('RGBA', t1.size, (120, 120, 120, 160)); sh.putalpha(t1.split()[3].point(lambda v: v * 0.5))
    x1 = 36; y1 = 52
    im.alpha_composite(sh, (x1 + 2, y1 + 2)); im.alpha_composite(t1, (x1, y1))
    f2 = ImageFont.truetype(XB, 22)
    t2 = styled_text('피에트로 왕자의 모험', f2, (30, 110, 200), (10, 70, 150),
                     (255, 255, 255, 255), 2, (40, 80, 130, 255), 1)
    x2 = 440 - t2.width; y2 = y1 + t1.height - 4
    im.alpha_composite(t2, (x2, y2))
    im = im.convert('RGB')
    im.save(os.path.join(ROOT, 'work/tmp/logo00_ko.png'))
    # quantize to 256 colours and write back
    q = im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:768]
    pal += [0] * (768 - len(pal))
    idx = bytes(q.getdata())
    cols = [(pal[3 * i], pal[3 * i + 1], pal[3 * i + 2], 0x80) for i in range(256)]
    # CSM1: stored order is swizzled
    stored = [None] * 256
    for i in range(256):
        j = (i & 0xe7) | ((i & 0x08) << 1) | ((i & 0x10) >> 1)
        stored[j] = cols[i]
    clut = b''.join(bytes(c) for c in stored)
    assert len(idx) == p.imgsize and len(clut) == p.clutsize
    d[p.imgoff:p.imgoff + p.imgsize] = idx
    d[p.clutoff:p.clutoff + p.clutsize] = clut
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(d)
    tm2.to_png(tm2.parse(bytes(d))[0], os.path.join(ROOT, 'work/tmp/logo00_check.png'))


if __name__ == '__main__':
    main()
