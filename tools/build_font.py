"""Rebuild the game fonts with Hangul glyphs.
usage: python tools/build_font.py OUTDIR
Keeps every non-kanji glyph of the original font, drops the kanji and adds the Hangul syllables
listed in work/hangul.txt at the codes given by kcode.  The full-width space and some punctuation
get narrower advances so that Korean word spacing looks natural.
"""
import os, sys, struct
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fnt import Fnt
import kcode

ROOT = kcode.ROOT
SRC = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/fonts')
TTF = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
TTF_HEAVY = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
FONTS = {  # name: (ttf, extra size tweak)
    'kanji12.fnt': (TTF_HEAVY, 0.0),
    'jk18_020.fnt': (TTF_HEAVY, 0.0),
    'menu24.fnt': (TTF_HEAVY, 0.0),
}
SS = 4  # supersampling
# advances (fraction of the kanji advance) for narrowed glyphs
NARROW = {'　': 0.40, '！': 0.42, '？': 0.55, '，': 0.36, '．': 0.36, '、': 0.40, '。': 0.45,
          '…': 0.80, '・': 0.40, '～': 0.70}


def cov_to_nib(a):
    if a < 0.07: return 0
    return max(1, min(15, int(round(16 - a * 15))))


def render_hangul(ttf, chars, W, H, asc):
    # pick a size whose Hangul ink height is H-1 px
    size = H * SS
    fnt = ImageFont.truetype(ttf, size)
    probe = '한글갈뷁'
    for _ in range(40):
        fnt = ImageFont.truetype(ttf, size)
        tops, bots, wid = [], [], []
        for ch in probe:
            b = fnt.getbbox(ch)
            tops.append(b[1]); bots.append(b[3]); wid.append(b[2] - b[0])
        ih = max(bots) - min(tops); iw = max(wid)
        if ih <= (H - 1) * SS and iw <= (W - 0.5) * SS: break
        size -= 1
    top = min(tops); inkh = max(bots) - top
    out = {}
    for ch in chars:
        im = Image.new('L', (W * SS, H * SS), 0)
        dr = ImageDraw.Draw(im)
        b = fnt.getbbox(ch)
        cw = b[2] - b[0]
        x = (W * SS - cw) / 2 - b[0]
        y = (H * SS - inkh) / 2 - top
        dr.text((x, y), ch, font=fnt, fill=255)
        sm = im.resize((W, H), Image.BOX)
        px = sm.load()
        out[ch] = [[cov_to_nib(px[x, y] / 255.0) for x in range(W)] for y in range(H)]
    return out


def build(name, outdir, hangul):
    f = Fnt(os.path.join(SRC, name))
    ttf, _ = FONTS[name]
    # reference kanji metrics
    ref = f.recs[f.codes.index(0x8d91)]  # 国
    W, ADV, ASC, DESC, BEAR = ref[0], ref[1], ref[2], ref[3], ref[4]
    H = ASC + DESC
    glyphs = []  # (code, rec, rows)
    for i, c in enumerate(f.codes):
        if c >= 0x889f: continue
        r = bytearray(f.recs[i]); rows = f.glyph(i)
        ch = bytes([c >> 8, c & 0xff]).decode('cp932', 'ignore') if c > 0xff else chr(c)
        if ch in NARROW:
            fr = NARROW[ch]
            na = max(1, int(round(ADV * fr)))
            if ch == '　':
                r[1] = na
            else:
                # trim empty columns and recentre in the new advance
                w = r[0]
                cols = [x for x in range(w) if any(row[x] for row in rows)] if rows and w else []
                if cols:
                    l, rr = cols[0], cols[-1] + 1
                    rows = [row[l:rr] for row in rows]
                    r[0] = rr - l
                    r[1] = max(na, r[0] + 1)
                    r[4] = (r[1] - r[0]) // 2 & 0xff
        glyphs.append((c, r, rows))
    if not any(g[0] == 0x20 for g in glyphs):
        r = bytearray(20); r[1] = max(1, int(round(ADV * 0.30))); r[2] = ASC; r[3] = DESC
        if f.fmt != 0: r[6] = 0x20
        glyphs.append((0x20, r, []))
    else:
        for g in glyphs:
            if g[0] == 0x20: g[1][1] = max(1, int(round(ADV * 0.30)))
    hmap = kcode.hangul_map()
    rend = render_hangul(ttf, hangul, W, H, ASC)
    for ch in hangul:
        c = hmap[ch]
        r = bytearray(ref)
        r[0] = W; r[1] = ADV - 2; r[2] = ASC; r[3] = DESC; r[4] = BEAR
        if f.fmt != 0: struct.pack_into('<H', r, 6, c)
        glyphs.append((c, r, rend[ch]))
    glyphs.sort(key=lambda g: g[0])
    # shelf packing
    tw = f.tw
    rowh = max(len(g[2]) for g in glyphs) + 1
    x = y = 0
    place = []
    for c, r, rows in glyphs:
        w = len(rows[0]) if rows else 0
        h = len(rows)
        if w == 0 or h == 0:
            place.append((0, 0, 0, 0)); continue
        if x + w > tw:
            x = 0; y += rowh
        place.append((x, y, x + w, y + h)); x += w + 1
    th = y + rowh
    if th > f.th:
        raise SystemExit('%s: texture overflow %d > %d (%d glyphs)' % (name, th, f.th, len(glyphs)))
    th = f.th
    tex = bytearray(tw * th // 2)
    for (c, r, rows), (x0, y0, x1, y1) in zip(glyphs, place):
        for yy, row in enumerate(rows):
            for xx, v in enumerate(row):
                px = x0 + xx; py = y0 + yy
                o = (py * tw + px) >> 1
                if px & 1: tex[o] = (tex[o] & 0x0f) | (v << 4)
                else: tex[o] = (tex[o] & 0xf0) | v
        if x1:
            f.set_rect(r, x0, y0, x1, y1)
        else:
            for k in range(8, 20): r[k] = 0
    f.recs = [g[1] for g in glyphs]
    f.codes = [g[0] for g in glyphs]
    f.tex = bytes(tex); f.th = th
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, name)
    f.save(dst)
    # keep the original file size so the heap layout of the game stays exactly as shipped
    osz = os.path.getsize(os.path.join(SRC, name)); nsz = os.path.getsize(dst)
    if nsz > osz:
        raise SystemExit('%s: font file grew %d > %d' % (name, nsz, osz))
    with open(dst, 'ab') as fo:
        fo.write(bytes(1) * (osz - nsz))
    return len(glyphs), y + rowh, f.th


if __name__ == '__main__':
    out = sys.argv[1]
    hangul = ''.join(open(kcode.HFILE, encoding='utf-8').read().split())
    for nm in FONTS:
        print(nm, build(nm, out, hangul))
