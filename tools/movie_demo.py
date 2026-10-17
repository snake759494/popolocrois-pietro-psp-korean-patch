"""Korean for the attract demos title_B1.pmf / title_E1.pmf.
* The Japanese title logo overlaid in the top-left corner (static) is inpainted away on every frame
  and replaced by Korean lettering with the same opacity.
* title_E1 shows recorded gameplay with dialogue boxes typing out Japanese: per scene the text
  pixels are inpainted away and the Korean line is typed out at the same pace.
usage: python tools/movie_demo.py title_E1 [--preview]"""
import os, sys, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import op_mux, movsample
from build_movies import encode, seconds

ROOT = movsample.ROOT
MOV = movsample.MOV
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/mov')
HEAVY = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')
EB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
FPS = 29.97
LOGO = (14, 18, 220, 46)          # Japanese part of the logo (PopoloCrois line below is kept)

E1_SCENES = [  # (start, end, speaker, korean)
    (3.0, 4.6, '문지기', '앗, 피에트로 왕자님! 무사하셨군요!\n지금 문을 열 테니\n잠깐만 기다려 주세요'),
    (49.6, 51.4, None, '기다려라'),
    (68.5, 70.2, '파울로 국왕', '너도 이제 남의 말을 알아들을 나이구나\n……사실대로 이야기해 주마'),
    (71.4, 72.68, '병사 곤', '잘됐네요, 피에트로 왕자님'),
    (72.68, 75.0, '병사 돈', '자, 왕가의 동굴까지지만\n둘이서 힘내 봅시다'),
    (75.5, 76.8, '로시모프', '알겠니?\n꽉 붙잡고 있어야 한다'),
    (76.8, 78.3, '질바', '던져 버리라니, 말도 안 돼\n파친코 구슬이 아니잖아'),
    (79.6, 80.8, '로시모프', '영차~'),
    (81.0, 99.0, '피에트로', '얼음 마왕……'),
]
TEXT = (82, 202, 398, 264)   # dialogue text area
TAG = (34, 173, 140, 197)    # name tag


def logo_layer():
    S = 3
    f = ImageFont.truetype(HEAVY, 21 * S)
    t = '포포로크로이스 이야기'
    im = Image.new('L', ((LOGO[2] - LOGO[0]) * S, (LOGO[3] - LOGO[1]) * S), 0)
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), t, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    sc = min(1, (im.width - 4 * S) / w)
    tmp = Image.new('L', (w + 8, h + 8), 0)
    ImageDraw.Draw(tmp).text((4 - bb[0], 4 - bb[1]), t, font=f, fill=255)
    tmp = tmp.crop(tmp.getbbox()).resize((int(w * sc), int(h * min(1, sc * 1.1))), Image.LANCZOS)
    im.paste(tmp, (2 * S, (im.height - tmp.height) // 2 + S))
    im = im.resize((LOGO[2] - LOGO[0], LOGO[3] - LOGO[1]), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    full = np.zeros((272, 480), np.float32)
    full[LOGO[1]:LOGO[3], LOGO[0]:LOGO[2]] = a
    return full


def do_logo(fr):
    x0, y0, x1, y1 = LOGO
    acc = np.zeros((272, 480), np.float32)
    step = max(1, len(fr) // 400)
    n = 0
    for i in range(0, len(fr), step):
        f = fr[i].astype(np.int16)
        acc += (f.min(2) > 150); n += 1
    core = acc / n > 0.55
    reg = np.zeros_like(core); reg[y0:y1, x0:x1] = True
    core &= reg
    mask = cv2.dilate(core.astype(np.uint8), np.ones((5, 5), np.uint8))
    a = logo_layer()
    cm = core
    for i in range(len(fr)):
        f = fr[i]
        lum = f.astype(np.float32).mean(2)
        bright = lum[cm].mean() if cm.any() else 0
        clean = cv2.inpaint(f, mask, 3, cv2.INPAINT_TELEA)
        bg = clean.astype(np.float32).mean(2)[cm].mean()
        op = np.clip((bright - bg) / 170.0, 0, 1)        # logo opacity follows the original
        aa = (a * op)[..., None]
        fr[i] = (clean.astype(np.float32) * (1 - aa) + 235 * aa).astype(np.uint8)
    return fr


def text_img(lines, font, size, area_w, lh):
    f = ImageFont.truetype(font, size * 2)
    W, H = area_w * 2, lh * 2 * max(1, len(lines)) + 8
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for k, l in enumerate(lines):
        d.text((0, k * lh * 2), l, font=f, fill=255)
    return im.resize((area_w, H // 2), Image.LANCZOS)


def textlike(lum):
    """dark strokes lying on bright parchment (not the dark box frame)"""
    around = cv2.blur(lum, (9, 9))
    return (lum < 110) & (around > 105)


def draw(ff, alpha, x, y, col=(30, 28, 36)):
    h, w = alpha.shape
    h = min(h, 272 - y); w = min(w, 480 - x)
    reg = ff[y:y + h, x:x + w]
    reg[:] = reg * (1 - alpha[:h, :w, None]) + np.array(col, np.float32) * alpha[:h, :w, None]


def do_dialogue(fr, scenes):
    fnt = ImageFont.truetype(EB, 12)
    meas = ImageDraw.Draw(Image.new('L', (1, 1)))
    for st, en, spk, ko in scenes:
        x0, y0, x1, y1 = TEXT; tx0, ty0, tx1, ty1 = TAG
        a0 = int(st * FPS); a1 = min(len(fr), int(en * FPS))
        vis_idx = [i for i in range(a0, a1)
                   if fr[i, y0 + 2:y1 - 6, x0 + 6:x1 - 4].astype(np.float32).mean() > 85]
        if not vis_idx: continue
        v0, v1 = vis_idx[0], vis_idx[-1] + 1
        plate = fr[v0:v1].max(0)
        pl = plate.astype(np.float32).mean(2)
        # characters already present in the first frame stay dark in the plate: inpaint them
        pm = np.zeros(pl.shape, np.uint8)
        med = cv2.medianBlur(pl.astype(np.uint8), 21).astype(np.float32)
        light = cv2.dilate((pl > 140).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        dark = (pl < med - 35) & light
        pm[y0 + 2:y1 - 4, x0 + 2:x1 - 6] = dark[y0 + 2:y1 - 4, x0 + 2:x1 - 6]
        tagfix = None
        if spk:
            sub = pl[ty0:ty1, tx0:tx1]
            lt = sub > max(105, np.percentile(sub, 55))
            if lt.any():
                col = np.median(plate[ty0:ty1, tx0:tx1][lt], axis=0)
                cols = np.where(lt.mean(0) > 0.35)[0]; rows = np.where(lt.mean(1) > 0.35)[0]
                if len(cols) and len(rows):
                    plate[ty0 + rows.min():ty0 + rows.max() + 1, max(tx0, tx0 + cols.min() - 7):tx0 + cols.max() + 1] = col
                    tagfix = (tx0 + cols.min() + 2, ty0 + rows.min() - 1)
        plate = cv2.inpaint(plate, cv2.dilate(pm, np.ones((3, 3), np.uint8)), 3, cv2.INPAINT_TELEA)
        # the first characters are typed in the very first frame: cover them with empty parchment
        ry0, ry1 = y0 + 2, y0 + 23
        plate[ry0:ry1, x0 + 2:x0 + 44] = plate[ry0:ry1, x1 - 70:x1 - 28]
        lines = ko.split(chr(10))
        body = text_img(lines, EB, 12, x1 - x0 - 4, 20)
        body_a = np.asarray(body, np.float32) / 255
        nchar = sum(len(l) for l in lines)
        dk = []
        for i in range(v0, v1):
            lum = fr[i].astype(np.float32).mean(2)
            dk.append(textlike(lum)[y0:y1, x0:x1].sum())
        prog = np.maximum.accumulate(np.array(dk, np.float32) / max(1, max(dk)))
        tag_a = None
        if spk:
            tag_a = np.asarray(text_img([spk], EB, 11, tx1 - tx0 + 40, 16), np.float32) / 255
        for j, i in enumerate(range(v0, v1)):
            f = fr[i].copy()
            f[y0:y1, x0:x1] = plate[y0:y1, x0:x1]
            if spk: f[ty0:ty1, tx0:tx1] = plate[ty0:ty1, tx0:tx1]
            ff = f.astype(np.float32)
            shown = int(round(prog[j] * nchar))
            cut = np.zeros_like(body_a); k = 0
            for li, l in enumerate(lines):
                if shown <= k: break
                take = min(len(l), shown - k)
                wpx = int(meas.textlength(l[:take], font=fnt)) + 3
                cut[li * 20:li * 20 + 20, :wpx] = 1
                k += len(l)
            draw(ff, body_a * cut, x0 + 6, y0 + 3)
            if tag_a is not None and tagfix:
                draw(ff, tag_a, tagfix[0], tagfix[1])
            fr[i] = ff.clip(0, 255).astype(np.uint8)
    return fr


def do_banner(fr, st, en, box, ko):
    x0, y0, x1, y1 = box
    a0, a1 = int(st * FPS), min(len(fr), int(en * FPS))
    tag = np.asarray(text_img([ko], EB, 12, x1 - x0, 18), np.float32) / 255
    for i in range(a0, a1):
        f = fr[i].copy()
        lum = f.astype(np.float32).mean(2)
        sub = lum[y0:y1, x0:x1]
        lt = sub > 120
        cols = np.where(lt.mean(0) > 0.45)[0]; rows = np.where(lt.mean(1) > 0.45)[0]
        if len(cols) < 20 or len(rows) < 6: continue
        col = np.median(f[y0:y1, x0:x1][lt], axis=0)
        f[y0 + rows.min():y0 + rows.max() + 1, x0 + cols.min():x0 + cols.max() + 1] = col
        vis = float(np.clip(np.median(lum[y0:y1, x0:x1][lt]) / 165.0, 0, 1))
        ff = f.astype(np.float32)
        draw(ff, tag * vis, x0 + cols.min() + 30, y0 + rows.min() - 2)
        fr[i] = ff.clip(0, 255).astype(np.uint8)
    return fr


def main(name):
    pmf = open(os.path.join(MOV, name + '.pmf'), 'rb').read()
    es = op_mux.video_es(pmf)
    keyint, _ = op_mux.gop(es)
    npy = os.path.join(ROOT, 'work/tmp/%s.npy' % name)
    fr = np.load(npy) if os.path.exists(npy) else movsample.frames(name)[0]
    fr = do_logo(fr)
    if name == 'title_E1':
        fr = do_dialogue(fr, E1_SCENES)
    if name == 'title_B1':
        fr = do_banner(fr, 47.2, 48.7, (180, 36, 345, 55), '모노케로스')
    for t in (47.9, 10, 4.2, 50.5, 69.8, 72.2, 73.9, 76.5, 77.6, 80.5, 83.6):
        i = min(len(fr) - 1, int(t * FPS))
        Image.fromarray(fr[i][:, :, ::-1]).save(os.path.join(ROOT, 'work/tmp/ko_%s_%04d.png' % (name, int(t * 10))))
    if '--preview' in sys.argv: return
    tmp = tempfile.mkdtemp(prefix='popodemo_')
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
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name + '.pmf'), 'wb').write(blob)
    shutil.rmtree(tmp, ignore_errors=True)
    print(name, 'kbps', kbps)


if __name__ == '__main__':
    main([a for a in sys.argv[1:] if not a.startswith('--')][0])
