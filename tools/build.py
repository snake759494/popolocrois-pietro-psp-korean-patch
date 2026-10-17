"""Full Korean patch build.
python tools/build.py [--noiso]
inputs : work/iso (extracted original), work/msg_occ.json, work/msg_src.json, work/boot_src.json,
         trans/out/*.json, trans/speakers.json, trans/telop/*.txt
outputs: work/build/... and the Korean ISO next to the original
"""
import os, sys, json, re, glob, struct, shutil, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kcode
from msgdb import R, ROOT
from msgpatch import repack

ORIG = os.path.join(ROOT, 'PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Japan) (v2.01).iso')
OUTISO = os.environ.get('OUTISO') or os.path.join(ROOT, 'PoPoLoCrois Monogatari - Pietro Ouji no Bouken (Korean).iso')
BUILD = os.path.join(ROOT, 'work/build')
TOK = re.compile(r'(\{[0-9a-f]{2}(?: [0-9a-f]{2})?\})')
log = []


def norm(s):
    s = s.replace(chr(92) + "n", chr(10)).replace(chr(13), "")
    s = s.replace('...', '…').replace('・・・', '…')
    s = s.replace('！', '!').replace('？', '?').replace('、', ', ').replace('。', '.')
    s = re.sub(r', (\n|$|\{)', r',\1', s)
    s = s.replace('〜', '~').replace('～', '~').replace('－', '-').replace('“', '"').replace('”', '"')
    return s


def load_trans():
    src = json.load(open(os.path.join(ROOT, 'work/msg_src.json'), encoding='utf-8'))
    tr = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'trans/out/[0-9]*.json'))):
        for k, v in json.load(open(f, encoding='utf-8')).items():
            tr[int(k)] = v
    fx = os.path.join(ROOT, 'trans/fix.json')
    if os.path.exists(fx):
        for k, v in json.load(open(fx, encoding='utf-8')).items(): tr[int(k)] = v
    m = {}
    for i, e in enumerate(src):
        if i in tr: m[e['jp']] = norm(tr[i])
    return m, len(src), len(tr)


def markup_bytes(s):
    out = b''
    for part in TOK.split(s):
        if not part: continue
        if TOK.fullmatch(part):
            out += bytes.fromhex(part[1:-1])
        else:
            out += kcode.encode_text(part)
    return out


def toks(s):
    return TOK.findall(s)


def collect_hangul(texts):
    hs = set()
    for t in texts:
        for c in t:
            if '가' <= c <= '힣' or 'ㄱ' <= c <= 'ㅣ': hs.add(c)
    ks = kcode.ksx1001()
    order = [c for c in ks if c in hs] + sorted(c for c in hs if c not in set(ks))
    return order


def main(noiso=False):
    tmap, nsrc, ntr = load_trans()
    speakers = json.load(open(os.path.join(ROOT, 'trans/speakers.json'), encoding='utf-8'))
    boot_tr = {}
    for f in glob.glob(os.path.join(ROOT, 'trans/out/boot*.json')):
        for k, v in json.load(open(f, encoding='utf-8')).items(): boot_tr[int(k)] = norm(v)
    telop = {}
    for f in glob.glob(os.path.join(ROOT, 'trans/telop/*.txt')):
        telop[os.path.basename(f)] = open(f, encoding='utf-8').read()
    print('messages translated %d/%d, boot %d, telop %d' % (ntr, nsrc, len(boot_tr), len(telop)))

    # ---- Hangul set & fonts
    extra = json.load(open(os.path.join(ROOT, 'trans/boot_extra.json'), encoding='utf-8'))['sjis']
    hs = collect_hangul(list(tmap.values()) + list(speakers.values()) + list(boot_tr.values()) + list(telop.values()) + list(extra.values()))
    print('hangul syllables', len(hs))
    os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
    open(kcode.HFILE, 'w', encoding='utf-8').write(''.join(hs))
    kcode._map = None
    import build_font
    fdir = os.path.join(BUILD, 'fonts')
    for nm in build_font.FONTS:
        print(' font', nm, build_font.build(nm, fdir, hs))

    patched = {}  # iso path -> bytes
    for nm in build_font.FONTS:
        patched['/PSP_GAME/USRDIR/data/fonts/' + nm] = open(os.path.join(fdir, nm), 'rb').read()

    # ---- message blocks
    occ = json.load(open(os.path.join(ROOT, 'work/msg_occ.json'), encoding='utf-8'))
    # blocks whose string area also holds other data (false positives) must never be repacked
    foreign = {(f, p) for f, p, *_ in json.load(open(os.path.join(ROOT, 'work/foreign.json')))}
    stats = collections.Counter(); overflow = []
    for f, blocks in occ.items():
        d = bytearray(open(R + f, 'rb').read())
        changed = False
        for p, keys in blocks:
            if (f, p) in foreign or all(k is None for k in keys): continue
            n, = struct.unpack_from('<H', d, p + 0x38)
            t, = struct.unpack_from('<I', d, p + 0x3c)
            news = []
            for i in range(n):
                idx, ln, off = struct.unpack_from('<HHI', d, p + t + 8 * i)
                orig = bytes(d[p + off:p + off + ln])
                k = keys[i]
                if k is None:
                    news.append(orig); continue
                spk, key, end = k
                ko = tmap.get(key)
                if ko is None:
                    stats['untranslated'] += 1; news.append(orig); continue
                if sorted(toks(ko)) != sorted(toks(key)):
                    log.append('token mismatch %s: %r -> %r' % (f, key, ko))
                    stats['tokmismatch'] += 1
                body = ko
                if spk is not None:
                    body = '{17}' + speakers.get(spk, spk) + '{18}' + body
                try:
                    b = markup_bytes(body) + bytes([end])
                except UnicodeEncodeError as e:
                    log.append('encode error %s: %r (%s)' % (f, body, e)); stats['encerr'] += 1
                    news.append(orig); continue
                news.append(b); stats['ok'] += 1
            ov = repack(d, p, news)
            if ov > 0:
                # reclaim space from developer-only debug strings of this block
                for i, s in enumerate(news):
                    if keys[i] is None and (s.startswith(b'DebugMessage') or s.startswith(b'\x81\xa6')):
                        news[i] = s[-1:]
                ov = repack(d, p, news)
            if ov > 0:
                overflow.append((f, p, ov))
                # fall back: keep the block untouched
                d2 = bytearray(open(R + f, 'rb').read())
                d[p:p + t + 8 * n] = d2[p:p + t + 8 * n]
                stats['overflow_blocks'] += 1
            else:
                changed = True
        if changed:
            orig = open(R + f, 'rb').read()
            allowed = bytearray(len(orig))
            for p2, keys2 in blocks:
                if (f, p2) in foreign or all(k is None for k in keys2): continue
                n2, = struct.unpack_from('<H', orig, p2 + 0x38); t2, = struct.unpack_from('<I', orig, p2 + 0x3c)
                lo2 = min(struct.unpack_from('<HHI', orig, p2 + t2 + 8 * j)[2] for j in range(n2))
                allowed[p2 + lo2:p2 + t2 + 8 * n2] = b'' * (t2 + 8 * n2 - lo2)
            bad = [k for k in range(len(orig)) if orig[k] != d[k] and not allowed[k]]
            assert len(d) == len(orig) and not bad, (f, len(bad))
            patched['/PSP_GAME/USRDIR/data/' + f] = bytes(d)
    print('messages', dict(stats))
    for o in overflow: print('  OVERFLOW', o)

    # ---- BOOT.BIN in place
    boot = bytearray(open(os.path.join(ROOT, 'work/iso/PSP_GAME/SYSDIR/BOOT.BIN'), 'rb').read())
    bsrc = {x['off']: x for x in json.load(open(os.path.join(ROOT, 'work/boot_src.json'), encoding='utf-8'))}
    bst = collections.Counter()
    for off, ko in boot_tr.items():
        x = dict(bsrc[off])
        if ko == x['jp']: bst['same'] += 1; continue
        if off in (0xdf9cc, 0xdf9e4, 0xe178c, 0xe1794, 0xe179c): bst['skip'] += 1; continue
        mm = re.match(r'([\x21-\x7e]+)', x['jp'])
        if mm and not ko.startswith(mm.group(1)) and '%' not in mm.group(1):
            # leading bytes belong to the preceding data, the text starts after them
            k = len(mm.group(1)); off += k; x['budget'] -= k; x['jp'] = x['jp'][k:]
        try:
            if chr(10) in x['jp']:
                ko = rewrap(ko, x['jp'])
            b = kcode.encode_text(ko)
        except UnicodeEncodeError as e:
            log.append('boot encode %x %r %s' % (off, ko, e)); bst['encerr'] += 1; continue
        if len(b) > x['budget']:
            log.append('boot overflow %x %d>%d %r' % (off, len(b), x['budget'], ko)); bst['overflow'] += 1; continue
        boot[off:off + x['budget'] + 1] = b + b'\0' * (x['budget'] + 1 - len(b))
        bst['ok'] += 1
    print('boot', dict(bst))
    extra_boot_patches(boot)
    patched['/PSP_GAME/SYSDIR/EBOOT.BIN'] = bytes(boot)
    patched['/PSP_GAME/SYSDIR/BOOT.BIN'] = bytes(boot)

    # ---- telop subtitles
    for name, txt in telop.items():
        patched['/PSP_GAME/USRDIR/data/telop/' + name] = encode_telop(txt)

    # ---- chapter title cards (pixels inside event files)
    cdir = os.path.join(ROOT, 'work/gfx_cards')
    if os.path.isdir(cdir):
        for fn in os.listdir(cdir):
            rel = 'evt/' + fn[:-4].replace('_', '/') + '.p01'
            key = '/PSP_GAME/USRDIR/data/' + rel
            d = bytearray(patched.get(key) or open(R + rel, 'rb').read())
            assert d[0x770:0x780] == bytes.fromhex('10200200000000001001000000020000')
            px = open(os.path.join(cdir, fn), 'rb').read()
            d[0x780:0x780 + len(px)] = px
            patched[key] = bytes(d)

    # ---- extra resources (images etc.)
    for iso_path, data in extra_files().items():
        patched[iso_path] = data

    open(os.path.join(ROOT, 'work/build_log.txt'), 'w', encoding='utf-8').write('\n'.join(log))
    print('log lines', len(log))
    if noiso: return
    from isobuild import Iso
    iso = Iso(ORIG, OUTISO)
    for pth, data in sorted(patched.items()):
        iso.replace(pth, data)
    iso.close()
    print('ISO written', OUTISO, os.path.getsize(OUTISO))


def _raw(s):
    return b''.join(c.encode('ascii') if ord(c) < 0x80 else kcode.enc_char(c) for c in s)


def telop_line(line):
    """timestamps / ASCII fields stay ASCII, the subtitle text is font-encoded"""
    out = []
    for fld in line.split(chr(9)):
        if re.fullmatch(r'[0-9:]*', fld):
            out.append(fld.encode('ascii'))
        else:
            pre = re.match(r'^!*', fld).group()
            out.append(pre.encode('ascii') + markup_bytes(fld[len(pre):].replace(' ', chr(0x3000))))
    return bytes([9]).join(out)



def encode_telop(txt):
    lines = txt.replace(chr(13), '').rstrip(chr(10)).split(chr(10))
    out = b''
    for line in lines:
        if line.startswith('[') or line.startswith('#'):
            b = _raw(line)
        else:
            b = telop_line(line)
        out += b + bytes([13, 10])
    return out



def extra_boot_patches(boot):
    """strings outside the main SJIS table: control-coded SJIS text and UTF-8 save-data strings"""
    ex = json.load(open(os.path.join(ROOT, 'trans/boot_extra.json'), encoding='utf-8'))
    for kind, items in ex.items():
        for off, ko in items.items():
            off = int(off, 16)
            end = boot.index(b'\0', off)
            e = end
            while e < len(boot) and boot[e] == 0: e += 1
            budget = e - off - 1
            b = markup_bytes(ko) if kind == 'sjis' else ko.encode('utf-8')
            if len(b) > budget:
                # UTF-8: cut at a character boundary
                if kind == 'utf8':
                    t = ko
                    while len(t.encode('utf-8')) > budget: t = t[:-1]
                    b = t.encode('utf-8')
                    log.append('boot utf8 trimmed %x %r' % (off, t))
                else:
                    log.append('boot extra overflow %x %d>%d' % (off, len(b), budget)); continue
            boot[off:off + budget + 1] = b + b'\0' * (budget + 1 - len(b))


def rewrap(ko, jp):
    """multi-line BOOT descriptions are drawn in fixed cells: keep every line within the
    widest original line (in characters) and within the original line count where possible"""
    jl = jp.split(chr(10))
    width = max(len(l) for l in jl)
    maxlines = max(len(jl), 3)
    parts = ko.split(chr(10))
    flat = parts[0]
    for nxt in parts[1:]:
        first = nxt.split(' ')[0]
        # a line break inside a word (e.g. a particle pushed to the next line) joins without a space
        glue = '' if (len(first.rstrip('.,!?')) == 1 and first[:1] in '은는이가을를의에도와과로만' and flat and '가' <= flat[-1] <= '힣' and '가' <= first[:1] <= '힣') or (flat and '가' <= flat[-1] <= '힣' and nxt[:1] in ('.', ',', '!', '?')) else ' '
        flat += glue + nxt
    words = flat.split()
    def wrap(ws, breakwords):
        lines, cur = [], ''
        for w in ws:
            cand = (cur + ' ' + w) if cur else w
            if len(cand) <= width:
                cur = cand; continue
            if cur: lines.append(cur); cur = ''
            while breakwords and len(w) > width:
                lines.append(w[:width]); w = w[width:]
            cur = w
        if cur: lines.append(cur)
        return lines
    lines = wrap(words, False)
    if len(lines) > maxlines or any(len(l) > width for l in lines):
        flat = ' '.join(words)
        lines = [flat[i:i + width].strip() for i in range(0, len(flat), width)]
    return chr(10).join(lines)


def patch_sfo(title):
    d = bytearray(open(os.path.join(ROOT, 'work/iso/PSP_GAME/PARAM.SFO'), 'rb').read())
    magic, ver, kt, dt, n = struct.unpack_from('<4sIIII', d, 0)
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 20 + 16 * i)
        k = d[kt + ko:d.index(b'\0', kt + ko)].decode()
        if k == 'TITLE':
            b = title.encode('utf-8') + b'\0'
            assert len(b) <= mx
            d[dt + do:dt + do + mx] = b + b'\0' * (mx - len(b))
            struct.pack_into('<I', d, 20 + 16 * i + 4, len(b))
    return bytes(d)


def extra_files():
    res = {}
    res['/PSP_GAME/PARAM.SFO'] = patch_sfo('포포로크로이스 이야기')
    gdir = os.path.join(ROOT, 'work/gfx_out')
    if os.path.isdir(gdir):
        for dp, _, fs in os.walk(gdir):
            for f in fs:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, gdir).replace(os.sep, '/')
                res['/PSP_GAME/' + rel] = open(p, 'rb').read()
    return res


if __name__ == '__main__':
    main('--noiso' in sys.argv)
