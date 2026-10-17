"""Hangul <-> SJIS code assignment and text encoding.
Hangul syllables are assigned to the SJIS kanji code area starting at 0x889F, in the order of
work/hangul.txt (the syllables used by the translation, KS X 1001 order first).
Word spaces use 0x8140 (full-width space, narrowed in the rebuilt fonts).
"""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HFILE = os.path.join(ROOT, 'work', 'hangul.txt')


def sjis_kanji_codes():
    for lead in list(range(0x88, 0xa0)) + list(range(0xe0, 0xeb)):
        for tr in list(range(0x40, 0x7f)) + list(range(0x80, 0xfd)):
            c = lead << 8 | tr
            if c < 0x889f: continue
            yield c


def ksx1001():
    out = []
    for hi in range(0xb0, 0xc9):
        for lo in range(0xa1, 0xff):
            out.append(bytes([hi, lo]).decode('cp949'))
    return out


_map = None


def hangul_map():
    global _map
    if _map is None:
        hs = open(HFILE, encoding='utf-8').read().split()
        hs = ''.join(hs)
        _map = dict(zip(hs, sjis_kanji_codes()))
    return _map


def reverse_map():
    return {v: k for k, v in hangul_map().items()}


# ASCII / misc -> full-width SJIS
FW = {'·': '・', '‥': '‥', '~': '～', '-': '－', "'": '’', '"': '”', '…': '…'}


def enc_char(ch):
    m = hangul_map()
    if ch in m:
        c = m[ch]; return bytes([c >> 8, c & 0xff])
    if ch in FW: ch = FW[ch]
    elif '!' <= ch <= '}':
        ch = chr(ord(ch) + 0xfee0)
    return ch.encode('cp932')


def encode_text(s):
    """plain text (no control tokens) -> bytes; ' ' -> 0x20, %s/%d format specs kept"""
    import re
    out = b''
    for part in re.split(r'(%[0-9]*[sd])', s):
        if part.startswith('%') and len(part) > 1:
            out += part.encode('ascii'); continue
        for c in part:
            out += c.encode('ascii') if c in ' \n&' else enc_char(c)
    return out


def decode_bytes(b):
    rm = reverse_map(); o = ''; j = 0
    while j < len(b):
        x = b[j]
        if 0x81 <= x <= 0x9f or 0xe0 <= x <= 0xfc:
            c = x << 8 | b[j + 1]
            o += rm.get(c) or b[j:j + 2].decode('cp932', 'replace'); j += 2
        else:
            o += chr(x); j += 1
    return o
