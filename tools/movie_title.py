"""Replace the burned-in Japanese narration of title_01.pmf with Korean.
For every caption: the Japanese text (white with a dark glow) is masked from the middle frame,
inpainted away on every frame of the caption, and the Korean line is drawn at the same place with
the same fade (opacity measured from the original text brightness). The closing message card
(dark text on white) is handled the same way with dark text.
The new H.264 stream goes back into the original PMF slots (op_mux), file size unchanged.
usage: python tools/movie_title.py [name] -> work/gfx_out/USRDIR/data/mov/<name>.pmf"""
import os, sys, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import op_mux, movsample
from build_movies import encode, seconds
from movcues import textmask

ROOT = movsample.ROOT
MOV = movsample.MOV
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/mov')
FONT_B = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
FONT_EB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
FPS = 29.97


def text_layer(text, size, color, glow, cx, cy, maxw=460, font=FONT_B, lh=None, sign=None):
    """RGBA float layers (a, rgb) 480x272 with centred multi-line text around (cx, cy)."""
    lines = text.split('\n')
    while True:
        f = ImageFont.truetype(font, size)
        d = ImageDraw.Draw(Image.new('L', (1, 1)))
        if max(d.textlength(l, font=f) for l in lines) <= maxw or size <= 9: break
        size -= 1
    lh = lh or int(size * 1.45)
    S = 2
    fS = ImageFont.truetype(font, size * S)
    im = Image.new('L', (480 * S, 272 * S), 0)
    dr = ImageDraw.Draw(im)
    total = lh * len(lines)
    y = cy - total / 2
    for l in lines:
        w = dr.textlength(l, font=fS) / S
        dr.text(((cx - w / 2) * S, y * S), l, font=fS, fill=255)
        y += lh
    if sign:
        fs = ImageFont.truetype(FONT_EB, int(size * 1.25) * S)
        w = dr.textlength(sign, font=fs) / S
        dr.text(((cx - w / 2) * S, (y + lh * 0.6) * S), sign, font=fs, fill=255)
    im = im.resize((480, 272), Image.LANCZOS)
    core = np.asarray(im, np.float32) / 255
    if glow is not None:
        g = np.asarray(im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
        a = np.maximum(core, g * 0.75)
        rgb = core[..., None] * np.array(color, np.float32) + (1 - core[..., None]) * np.array(glow, np.float32)
    else:
        a = core
        rgb = np.ones((272, 480, 1), np.float32) * np.array(color, np.float32)
    return a, rgb


def process(fr, cues, subs):
    by = {s['cue']: s for s in subs}
    for c in cues_sel(cues, by):
        s = by[c['k']]
        m = c['mid']
        x0, y0, x1, y1 = c['box']
        x0 -= 6; y0 -= 6; x1 += 6; y1 += 6
        if s.get('end'):
            x0, y0, x1, y1 = 15, 50, 465, 215
        else:
            x0, y0, x1, y1 = 15, max(0, y0 - 30), 465, min(272, y1 + 14)
        i0 = int(c['start'] * FPS); i1 = int(c['end'] * FPS)
        q0 = i0 + (i1 - i0) // 4; q1 = i1 - (i1 - i0) // 4
        acc = np.zeros(fr[0].shape[:2], np.float32)
        for i in range(q0, q1):
            if s.get('end'):
                acc += (fr[i].astype(np.float32).mean(2) < 205)
            else:
                acc += textmask(fr[i], 185)
        core = acc / max(1, q1 - q0) > 0.3
        reg = np.zeros(core.shape, bool); reg[y0:y1, x0:x1] = True
        core &= reg
        mask = cv2.dilate(core.astype(np.uint8), np.ones((7, 7), np.uint8))
        a0 = max(0, int((c['start'] - 1.0) * FPS)); a1 = min(len(fr), int((c['end'] + 1.0) * FPS) + 1)
        ref_l = None
        if s.get('end'):
            a, rgb = text_layer(s['ko'], 13, (70, 45, 30), None, 240, 112, sign=s.get('sign'))
        else:
            ys = np.where(core.any(1))[0]
            a, rgb = text_layer(s['ko'], 12, (245, 245, 245), (20, 20, 20), 240, (ys.min() + ys.max()) / 2)
        # opacity of the original caption per frame
        cm = core.astype(bool)
        vals = []
        for i in range(a0, a1):
            f = fr[i]
            clean = cv2.inpaint(f, mask, 4, cv2.INPAINT_TELEA)
            diff = np.abs(f.astype(np.float32) - clean.astype(np.float32)).mean(2)[cm].mean()
            vals.append(diff)
            fr[i] = clean
        ref = max(vals) if vals else 1
        for j, i in enumerate(range(a0, a1)):
            op = min(1.0, vals[j] / ref * 1.15) if ref > 0 else 0
            if op < 0.04: continue
            aa = (a * op)[..., None]
            f = fr[i].astype(np.float32)
            fr[i] = (f * (1 - aa) + rgb[..., ::-1] * aa).clip(0, 255).astype(np.uint8)
    return fr


def cues_sel(cues, by):
    out = []
    for k, c in enumerate(cues):
        if k in by:
            c = dict(c); c['k'] = k; out.append(c)
    return out


def main(name='title_01'):
    subs = json.load(open(os.path.join(ROOT, 'trans/movie_subs.json'), encoding='utf-8'))[name]
    cues = json.load(open(os.path.join(ROOT, 'work/tmp/cues_%s.json' % name)))
    pmf = open(os.path.join(MOV, name + '.pmf'), 'rb').read()
    es = op_mux.video_es(pmf)
    keyint, _ = op_mux.gop(es)
    fr = np.load(os.path.join(ROOT, 'work/tmp/%s.npy' % name))
    fr = process(fr, cues, subs)
    for t in (5, 13, 26, 40, 52, 62, 79):
        Image.fromarray(fr[int(t * FPS)][:, :, ::-1]).save(os.path.join(ROOT, 'work/tmp/ko_%s_%02d.png' % (name, t)))
    if '--preview' in sys.argv: return
    tmp = tempfile.mkdtemp(prefix='popomov_')
    kbps = max(200, int(len(es) * 0.97 * 8 / seconds(pmf) / 1000))
    for attempt in range(14):
        out = os.path.join(tmp, 'out.264')
        encode(fr, out, tmp, keyint, kbps)
        new = open(out, 'rb').read()
        try:
            blob = op_mux.build(pmf, new)[0]; break
        except ValueError as e:
            if 'lower the bitrate' not in str(e): raise
            kbps = int(kbps * 0.92)
    else:
        raise SystemExit('does not fit')
    assert len(blob) == len(pmf)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name + '.pmf'), 'wb').write(blob)
    shutil.rmtree(tmp, ignore_errors=True)
    print(name, 'kbps', kbps)


if __name__ == '__main__':
    main(*[a for a in sys.argv[1:] if not a.startswith('--')])
