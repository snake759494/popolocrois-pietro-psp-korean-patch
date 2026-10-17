"""Rewrite the strings of a message block in place.
All strings of a block live between the lowest string offset and the table; they are repacked
there (the '$' padding is reclaimed).  Returns overflow bytes (0 = ok)."""
import struct


def region(d, p):
    n, = struct.unpack_from('<H', d, p + 0x38)
    t, = struct.unpack_from('<I', d, p + 0x3c)
    ents = [struct.unpack_from('<HHI', d, p + t + 8 * i) for i in range(n)]
    lo = min(e[2] for e in ents)
    return n, t, ents, lo


def repack(d, p, news):
    """d: bytearray (whole file); p: block offset; news: list of bytes (each incl. end code, w/o 00)
    returns needed - available (<=0 ok)"""
    n, t, ents, lo = region(d, p)
    assert len(news) == n
    # identical strings share storage
    blob = bytearray(); offs = {}; table = []
    for s in news:
        if s not in offs:
            offs[s] = lo + len(blob); blob += s + b'\0'
        table.append((len(s), offs[s]))
    avail = t - lo
    if len(blob) > avail:
        return len(blob) - avail
    blob += b'$' * (avail - len(blob))
    d[p + lo:p + t] = blob
    for i, (ln, off) in enumerate(table):
        struct.pack_into('<HHI', d, p + t + 8 * i, i, ln, off)
    return len(blob.rstrip(b'$')) - avail
