"""Extract every message-block string into the translation DB.
work/msg_occ.json : {file: [[block_off, [key or null per entry]]]}
trans/db.json     : {key: {"jp": markup, "n": occurrences, "src": first file}}
markup: text with "\n" newlines, control bytes as {xx} / {xx yy}, speaker names as {17}NAME{18}
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgdb import R, ROOT, entries

ARG1 = {0x10, 0x14, 0x15, 0x16, 0x19}   # control codes taking one argument byte


def to_markup(s):
    """bytes (with end code) -> markup or None if not text"""
    if not s: return None
    # most strings end with their end code (0x13 / 0x1A); some tables store the length without it
    body = s[:-1] if s[-1] in (0x13, 0x1a) else s
    o = ''; j = 0
    while j < len(body):
        b = body[j]
        if 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc:
            if j + 1 >= len(body): return None
            try:
                o += body[j:j + 2].decode('cp932')
            except UnicodeDecodeError:
                return None
            j += 2
        elif b == 0x0a:
            o += '\n'; j += 1
        elif b in ARG1:
            if j + 1 >= len(body): return None
            o += '{%02x %02x}' % (b, body[j + 1]); j += 2
        elif b in (0x09, 0x0c, 0x12, 0x17, 0x18):
            o += '{%02x}' % b; j += 1
        elif 0xa1 <= b <= 0xdf:
            o += bytes([b]).decode('cp932'); j += 1      # half-width katakana / '･'
        elif 0x20 <= b < 0x7f and b not in (0x7b, 0x7d):
            o += chr(b); j += 1
        else:
            return None
    return o


def main():
    blocks = json.load(open(os.path.join(ROOT, 'work/blocks.json')))
    db = collections.OrderedDict(); occ = {}
    names = collections.Counter()
    for f in sorted(blocks, key=lambda x: (not x.startswith('evt'), x)):
        d = open(R + f, 'rb').read()
        occ[f] = []
        for p, n, t in blocks[f]:
            keys = []
            for ln, off, s in entries(d, p):
                m = to_markup(s)
                if m is None or not re.search('[぀-ヿ一-鿿！-～]', m) or m.startswith('DebugMessage'):
                    keys.append(None); continue
                m2 = m
                mm = re.match(r'\{17\}(.*?)\{18\}', m)
                if mm:
                    names[mm.group(1)] += 1
                    m2 = m[mm.end():]
                    key = m2
                else:
                    key = m2
                e = db.get(key)
                if e is None:
                    e = db[key] = {'jp': key, 'n': 0, 'src': f}
                e['n'] += 1
                keys.append([mm.group(1) if mm else None, key, s[-1] if s[-1] in (0x13, 0x1a) else -1])
            occ[f].append([p, keys])
    os.makedirs(os.path.join(ROOT, 'trans'), exist_ok=True)
    json.dump(occ, open(os.path.join(ROOT, 'work/msg_occ.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(list(db.values()), open(os.path.join(ROOT, 'work/msg_src.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(names.most_common(), open(os.path.join(ROOT, 'work/speakers.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('unique', len(db), 'chars', sum(len(e['jp']) for e in db.values()), 'speakers', len(names))


if __name__ == '__main__':
    main()
