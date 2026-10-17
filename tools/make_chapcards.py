"""Korean chapter title cards. Erases the Japanese lettering (inpaint) and draws Korean text in the
same cream colour with a soft dark shadow; pixels are mapped back to the card's own palette."""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chapcard import CARDS, load, PAL, PIX, W, H, ROOT

OUT = os.path.join(ROOT, 'work/gfx_cards')
HEAVY = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')
EB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')
ARC = ['얼음 마왕 편'] * 4 + ['어둠의 사자왕 편'] * 3 + ['여신 마이라 편'] * 5
CH = ['제1장', '제2장', '제3장', '제4장', '제1장', '제2장', '제3장', '제1장', '제2장', '제3장', '제4장', '에필로그']
SUB = ['~피에트로의 여행~', '~어둠의 세계로~', '~하얀 대지~', '~작은 평온~',
       '~왕위 계승식~', '~여신의 계략~', '~유적의 섬~',
       '~대지의 용~', '~봉인의 석판~', '~요정왕의 호수~', '~어둠의 눈뜸~', '~소중한 마음~']
TITLE_BOX = (55, 56, 262, 106)
SUB_BOX = (170, 158, 424, 214)


def erase(rgb, box):
    x0, y0, x1, y1 = box
    sub = rgb[y0:y1, x0:x1].astype(np.float32)
    med = cv2.medianBlur(rgb, 21)[y0:y1, x0:x1].astype(np.float32)
    diff = np.abs(sub - med).sum(2)
    m = np.zeros(rgb.shape[:2], np.uint8)
    m[y0:y1, x0:x1] = diff > 20
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    return cv2.inpaint(rgb, m, 5, cv2.INPAINT_TELEA)


def draw_text(img, text, font, size, x, y, anchor_right=None):
    S = 3
    f = ImageFont.truetype(font, size * S)
    bb = f.getbbox(text)
    lay = Image.new('L', (bb[2] - bb[0] + 12 * S, bb[3] - bb[1] + 12 * S), 0)
    ImageDraw.Draw(lay).text((6 * S - bb[0], 6 * S - bb[1]), text, font=f, fill=255)
    lay = lay.resize((lay.width // S, lay.height // S), Image.LANCZOS)
    a = np.asarray(lay, np.float32) / 255
    sh = np.asarray(lay.filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    if anchor_right is not None: x = anchor_right - lay.width + 6
    h, w = a.shape
    reg = img[y:y + h, x:x + w].astype(np.float32)
    sx = np.zeros_like(sh); sx[2:, 2:] = sh[:-2, :-2]
    reg = reg * (1 - sx[..., None] * 0.65)
    reg = reg * (1 - a[..., None]) + np.array([238, 236, 205], np.float32) * a[..., None]
    img[y:y + h, x:x + w] = reg.clip(0, 255).astype(np.uint8)


def to_index(rgb, pal):
    p = pal[:, :3].astype(np.int32)
    flat = rgb.reshape(-1, 3).astype(np.int32)
    out = np.empty(len(flat), np.uint8)
    for s in range(0, len(flat), 8192):
        blk = flat[s:s + 8192]
        out[s:s + 8192] = ((blk[:, None, :] - p[None]) ** 2).sum(-1).argmin(1)
    return out.reshape(H, W)


def main():
    os.makedirs(os.path.join(ROOT, 'work/tmp'), exist_ok=True)
    sheet = Image.new('RGB', (W * 2, H * 6))
    for k, n in enumerate(CARDS):
        d, pal, ix = load(n)
        orig_ix = ix.copy()
        rgb = pal[ix][..., :3].copy()
        rgb = erase(rgb, TITLE_BOX)
        rgb = erase(rgb, SUB_BOX)
        draw_text(rgb, ARC[k], HEAVY, 25, 62, 60)
        draw_text(rgb, CH[k], HEAVY, 13, 196, 162)
        draw_text(rgb, SUB[k], HEAVY, 19, 188, 178)
        new = to_index(rgb, pal)
        # only touch the text regions
        keep = np.ones((H, W), bool)
        for x0, y0, x1, y1 in (TITLE_BOX, SUB_BOX):
            keep[y0 - 4:y1 + 8, x0 - 4:x1 + 2] = False
        new[keep] = orig_ix[keep]
        os.makedirs(OUT, exist_ok=True)
        open(os.path.join(OUT, n.replace('/', '_') + '.bin'), 'wb').write(new.tobytes())
        sheet.paste(Image.fromarray(pal[new][..., :3]), ((k % 2) * W, (k // 2) * H))
    sheet.resize((W, H * 3)).save(os.path.join(ROOT, 'work/tmp/cards_ko.png'))


if __name__ == '__main__':
    main()
