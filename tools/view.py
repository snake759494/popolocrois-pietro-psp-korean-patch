import sys
from PIL import Image
f, off, w, bpp, swz, h = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
d = open(f, 'rb').read()[off:]
bw = w * bpp // 8
d = d[:bw * h]
h = len(d) // bw
d = d[:bw * h]
if swz:
    out = bytearray(len(d)); i = 0
    for by in range(h // 8):
        for bx in range(bw // 16):
            for r in range(8):
                o = (by * 8 + r) * bw + bx * 16
                out[o:o + 16] = d[i:i + 16]; i += 16
    d = bytes(out)
px = bytearray()
if bpp == 4:
    for x in d: px += bytes([(x & 15) * 17, (x >> 4) * 17])
elif bpp == 8:
    px = d
elif bpp == 2:
    for x in d: px += bytes([((x >> s) & 3) * 85 for s in (0, 2, 4, 6)])
elif bpp == 1:
    for x in d: px += bytes([((x >> s) & 1) * 255 for s in range(8)])
Image.frombytes('L', (w, h), bytes(px)).save(sys.argv[7])
