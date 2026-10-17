"""Redraw the Japanese name labels of gui/msg_00.tm2 and gui/car_00.tm2 in Korean.
Labels use a brightness ramp in the 4bpp indices (15 = white fill, 1-3 = dark shadow), so we draw
white text with a 1px dark shadow and write the indices directly; every palette keeps working."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tm2

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GUI = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/gui')
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/gui')
FONT = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')
SLOT = 11

RIGHT = [('피에트로', '백기사'), ('나르시아', '질바'), ('가미가미', '레오나'), ('귀면동자', '엘레나'),
         ('다이슨', '로빈'), ('레파드', '도그마'), ('미샤', '자파'), ('타모타모', '쿠르트'),
         ('유키토코', '밀트'), ('뿔문어', '보리스'), ('날쌘고양', '라우라'), ('카론', '무사시'),
         ('돈 마에스트로',), ('어릿광대 인형',), ('말미잘',), ('킹 터틀',), ('허밍 플라이',),
         ('룬 윙',), ('리틀 라이더',), ('화이트 시프',), ('이블 페이스',)]
RIGHT_Y = [1, 13, 25, 37, 50, 62, 74, 86, 98, 109, 121, 134, 146, 158, 169, 181, 194, 205, 218, 229, 242]
BOTTOM = [(97, [(8, '버닝 호스'), (8, '레서 데몬')]),
          (109, [(8, '오크 파이터'), (8, '천사 드론')]),
          (121, [(6, '이블 나이트'), (6, '전투벌'), (4, '시저')]),
          (133, [(5, '플래시'), (5, '칵테스'), (5, '가우메일')]),
          (145, [(5, '궁수'), (3, '나오토'), (7, '에너지 소울')])]


def render(text, w, h=10, font=None):
    """returns {(x,y): index} for a label fitted into w x h (+1px shadow)"""
    S = 4
    f = ImageFont.truetype(font or FONT, 11 * S)
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    im = Image.new('L', (tw + 4 * S, th + 4 * S), 0)
    ImageDraw.Draw(im).text((2 * S - bb[0], 2 * S - bb[1]), text, font=f, fill=255)
    im = im.crop(im.getbbox())
    tw2 = min(w - 1, max(1, round(im.width / S)))
    th2 = min(h - 1, round(im.height / S))
    sm = im.resize((tw2, th2), Image.BOX)
    px = sm.load()
    ox = (w - 1 - tw2) // 2; oy = (h - 1 - th2) // 2
    out = {}
    for y in range(th2):
        for x in range(tw2):
            a = px[x, y] / 255
            if a > 0.25:
                out[(ox + x, oy + y)] = 15 if a > 0.6 else 11
    for (x, y), v in list(out.items()):
        for dx, dy in ((1, 1), (1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in out and q[0] < w and q[1] < h:
                out[q] = 2
    return out


def apply(ix, W, x0, y0, w, h, text, font=None):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            ix[y * W + x] = 0
    if text:
        for (x, y), v in render(text, w, h, font).items():
            ix[(y0 + y) * W + x0 + x] = v


def save(name, p, d, ix):
    img = bytearray(len(ix) // 2)
    for i in range(0, len(ix), 2):
        img[i // 2] = ix[i] | (ix[i + 1] << 4)
    d[p.imgoff:p.imgoff + p.imgsize] = img
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), 'wb').write(d)


def grid_labels(ix, W, xbase, ybase, rows_y, rows):
    for ry, cells in zip(rows_y, rows):
        if len(cells) == 2:
            spans = [(xbase, 4 * SLOT, cells[0]), (xbase + 4 * SLOT, 3 * SLOT, cells[1])]
        else:
            spans = [(xbase, 7 * SLOT, cells[0])]
        for x, w, t in spans:
            apply(ix, W, x, ybase + ry - 1, min(w, W - x), 11, t)


def main():
    # msg_00
    d = bytearray(open(os.path.join(GUI, 'msg_00.tm2'), 'rb').read())
    p = tm2.parse(bytes(d))[0]; ix = tm2.indices(p); W = p.w
    grid_labels(ix, W, 176, 0, RIGHT_Y, RIGHT)
    for y, cells in BOTTOM:
        x = 0
        for n, t in cells:
            apply(ix, W, x, y - 1, n * SLOT, 11, t); x += n * SLOT
    apply(ix, W, 0, 157, 62, 18, '가득')            # いっぱい
    apply(ix, W, 145, 1, 17, 15, '개')               # 個
    apply(ix, W, 128, 17, 23, 11, '가보'); apply(ix, W, 152, 17, 24, 11, '곤')
    apply(ix, W, 128, 29, 23, 11, '돈'); apply(ix, W, 152, 29, 24, 11, '멜')
    apply(ix, W, 128, 41, 34, 15, '합계')
    apply(ix, W, 128, 57, 24, 11, '카이')
    save('msg_00.tm2', p, d, ix)
    # car_00 : same 11px grid at x=145, rows 89/101/113/125, plus ガボ/ゴン/ドン and カイ
    d = bytearray(open(os.path.join(GUI, 'car_00.tm2'), 'rb').read())
    p = tm2.parse(bytes(d))[0]; ix = tm2.indices(p); W = p.w
    grid_labels(ix, W, 145, 0, [89, 101, 113, 125], RIGHT[:4])
    apply(ix, W, 222, 88, 30, 12, '가보'); apply(ix, W, 222, 100, 30, 12, '곤')
    apply(ix, W, 222, 112, 30, 12, '돈')
    apply(ix, W, 199, 63, 28, 14, '카이')
    save('car_00.tm2', p, d, ix)


if __name__ == '__main__':
    main()
