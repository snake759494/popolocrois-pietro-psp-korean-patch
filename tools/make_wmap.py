"""Korean world-map labels: gui/wmap/map_01.tm2 (place names, grey ramp) and map_00.tm2 (region plates)."""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tm2
from make_labels import apply, save

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR/data/gui/wmap')
OUT = os.path.join(ROOT, 'work/gfx_out/USRDIR/data/gui/wmap')
EB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
RG = os.path.join(ROOT, 'NanumSquareNeo-bRg.ttf')
BD = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')

PLACES = [
    (0, [(1, 120, '포포로크로이스 성하마을'), (130, 212, '가미가미 마왕성')]),
    (14, [(1, 96, '포포로크로이스 성'), (102, 124, '갱도'), (130, 200, '브리오니아 성')]),
    (28, [(2, 72, '달음박질 샘'), (78, 124, '산악 지대'), (130, 224, '라닥 선인의 암자')]),
    (42, [(2, 60, '타키넨 마을'), (66, 124, '원숭이 제국'), (129, 176, '폭포 뒤 동굴'), (181, 228, '요정의 숲')]),
    (56, [(2, 60, '길다의 집'), (66, 124, '하타하타 마을'), (131, 212, '우구이스 성하마을')]),
    (70, [(1, 60, '왕가의 동굴'), (66, 124, '만셀 마을'), (130, 212, '로마나 성하마을')]),
    (84, [(2, 72, '우라노스 광장'), (78, 124, '파세라'), (130, 188, '로마나 성')]),
    (98, [(2, 83, '서커스 텐트'), (88, 122, '하얀 마을'), (129, 188, '강철 마왕성')]),
    (112, [(1, 84, '수몰 브리오니아'), (89, 124, '용의 나라'), (129, 188, '노룡신의 성')]),
    (126, [(2, 96, '얀의 대포 연구소'), (103, 160, '레오나의 집')]),
    (140, [(2, 72, '로마나 철도'), (77, 124, '봉인의 탑'), (129, 176, '요정의 성')]),
    (154, [(1, 46, '해안 거리'), (52, 122, '고드리프 광산'), (129, 187, '다나 신전')]),
    (168, [(2, 96, '가미가미 신마왕성'), (103, 160, '우구이스 성')]),
    (182, [(2, 96, '고드리프 터널'), (101, 159, '용의 사당')]),
    (196, [(2, 84, '훈바훈바 마을'), (90, 148, '마이라 신전')]),
    (210, [(2, 60, '정글'), (65, 112, '얼음 신전'), (118, 188, '몬스터 마을')]),
    (224, [(2, 60, '코트리코 섬'), (66, 112, '철의 무덤'), (117, 176, '폴레폴레 마을')]),
    (238, [(1, 48, '온천 동굴'), (54, 133, '가미가미 시티'), (142, 188, '마왕의 별')]),
]
PLATES = [  # (x0, y0, x1, y1, korean)
    (0, 24, 143, 48, '포포로크로이스 지방'), (144, 24, 244, 48, '만셀 지방'),
    (0, 48, 114, 72, '로마나 지방 북부'), (116, 48, 231, 72, '로마나 지방 남부'),
    (0, 72, 71, 96, '고드리프'), (72, 72, 171, 96, '파세라 지방'), (172, 72, 243, 96, '산악 지대'),
    (0, 96, 59, 120, '북쪽 산'), (61, 96, 159, 120, '레무리아 대륙'), (160, 96, 248, 120, '코트리코 섬'),
    (0, 120, 86, 144, '하타하타 마을'), (88, 120, 159, 144, '요정의 숲'), (160, 120, 233, 144, '빙원 지대'),
    (0, 144, 87, 168, '정글'), (88, 144, 148, 168, '해의 나라'),
]


def places():
    d = bytearray(open(os.path.join(SRC, 'map_01.tm2'), 'rb').read())
    p = tm2.parse(bytes(d))[0]; ix = tm2.indices(p); W = p.w
    for y, labs in PLACES:
        for x0, x1, t in labs:
            apply(ix, W, max(0, x0 - 1), max(0, y - 1), min(W - x0 + 1, x1 - x0 + 4), 13, t, RG)
    out = OUT
    os.makedirs(out, exist_ok=True)
    img = bytearray(len(ix) // 2)
    for i in range(0, len(ix), 2): img[i // 2] = ix[i] | (ix[i + 1] << 4)
    d[p.imgoff:p.imgoff + p.imgsize] = img
    open(os.path.join(out, 'map_01.tm2'), 'wb').write(d)


def plates():
    d = bytearray(open(os.path.join(SRC, 'map_00.tm2'), 'rb').read())
    p = tm2.parse(bytes(d))[0]
    ix = np.array(tm2.indices(p)[:p.w * p.h], np.uint8).reshape(p.h, p.w)
    pal = np.array([tuple(p.clut[4 * i:4 * i + 4]) for i in range(16)], np.int32)
    rgb = pal[ix][..., :3].astype(np.uint8)
    lum = rgb.astype(np.float32).mean(2)
    S = 4
    for x0, y0, x1, y1, t in PLATES:
        ix0, iy0, ix1, iy1 = x0 + 5, y0 + 4, x1 - 5, y1 - 4
        m = np.zeros(lum.shape, np.uint8)
        sub = lum[iy0:iy1, ix0:ix1]
        m[iy0:iy1, ix0:ix1] = (sub < 75)
        m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        m[:iy0, :] = 0; m[iy1:, :] = 0; m[:, :ix0] = 0; m[:, ix1:] = 0
        rgb = cv2.inpaint(rgb, m, 3, cv2.INPAINT_TELEA)
        # text: crisp (binary) dark letters with a 1px light outline, like the original plates
        w, h = ix1 - ix0, iy1 - iy0
        size = 13
        while True:
            f = ImageFont.truetype(BD, size)
            bb = f.getbbox(t)
            if (bb[2] - bb[0] <= w - 4 and bb[3] - bb[1] <= h - 2) or size <= 9: break
            size -= 1
        im = Image.new('L', (w, h), 0)
        ImageDraw.Draw(im).text(((w - (bb[2] - bb[0])) // 2 - bb[0], (h - (bb[3] - bb[1])) // 2 - bb[1]), t, font=f, fill=255)
        core = np.asarray(im, np.uint8) > 110
        rim = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~core
        reg = rgb[iy0:iy1, ix0:ix1]
        reg[rim] = (205, 170, 80)
        reg[core] = (40, 22, 10)
        # back to palette 0 indices inside the plate
        blk = rgb[y0:y1, x0:x1].astype(np.int32)
        dist = ((blk[..., None, :] - pal[None, None, 1:, :3]) ** 2).sum(-1)
        ix[y0:y1, x0:x1] = np.where(ix[y0:y1, x0:x1] == 0, 0, dist.argmin(-1) + 1)
    flat = ix.reshape(-1)
    img = bytearray(len(flat) // 2)
    for i in range(0, len(flat), 2): img[i // 2] = int(flat[i]) | (int(flat[i + 1]) << 4)
    d[p.imgoff:p.imgoff + p.imgsize] = img
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'map_00.tm2'), 'wb').write(d)


if __name__ == '__main__':
    places(); plates()
    from PIL import Image as I
    o = I.new('RGBA', (1024, 512), (40, 40, 70, 255))
    for k, n in enumerate(['map_00', 'map_01']):
        p = tm2.parse(open(os.path.join(OUT, n + '.tm2'), 'rb').read())[0]
        im = tm2.to_png(p, os.path.join(ROOT, 'work/tmp/_w.png'), 0)
        bg = I.new('RGBA', im.size, (40, 40, 70, 255)); bg.alpha_composite(im)
        o.paste(bg.resize((512, 512), I.NEAREST), (k * 512, 0))
    o.save(os.path.join(ROOT, 'work/tmp/wmap_ko.png'))
