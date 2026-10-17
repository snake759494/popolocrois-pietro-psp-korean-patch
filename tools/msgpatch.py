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


def repack_slots(d, p, news):
    """Blocks whose string area also holds other data: reuse only the bytes the original strings
    (and their NUL/'$' padding runs) occupied. Each new string goes first-fit into one free hole.
    Returns number of strings that did not fit (those keep their original text)."""
    n, t, ents, lo = region(d, p)
    holes = []
    for idx, ln, off in sorted(ents, key=lambda e: e[2]):
        a = off; b = off + ln + 1
        while b < t and d[p + b] in (0x24,): b += 1
        if holes and a <= holes[-1][1]:
            holes[-1][1] = max(holes[-1][1], b)
        else:
            holes.append([a, b])
    orig = {e[2]: bytes(d[p + e[2]:p + e[2] + e[1]]) for e in ents}
    placed = {}; fail = 0
    for i, s in enumerate(news):
        if s in placed: continue
        need = len(s) + 1
        for h in holes:
            if h[1] - h[0] >= need:
                placed[s] = h[0]; h[0] += need; break
    table = []
    for i, s in enumerate(news):
        if s not in placed:
            s = orig[ents[i][2]]; fail += 1
            if s not in placed:
                for h in holes:
                    if h[1] - h[0] >= len(s) + 1:
                        placed[s] = h[0]; h[0] += len(s) + 1; break
        table.append((len(s), placed[s], s))
    # clear the old string bytes, then write
    for idx, ln, off in ents:
        a = off; b = off + ln + 1
        d[p + a:p + b] = b'\0' * (b - a)
    for ln, off, s in table:
        d[p + off:p + off + ln + 1] = s + b'\0'
    for i, (ln, off, s) in enumerate(table):
        struct.pack_into('<HHI', d, p + t + 8 * i, ents[i][0], ln, off)
    return fail


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
        struct.pack_into('<HHI', d, p + t + 8 * i, ents[i][0], ln, off)
    return len(blob.rstrip(b'$')) - avail
