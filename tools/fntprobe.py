import struct, sys
d = open(sys.argv[1], 'rb').read()
print(d[:8].hex(), len(d))
start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 8
rs = int(sys.argv[3], 0) if len(sys.argv) > 3 else 20
i = start; n = 0; prev = -1
while i + rs <= len(d):
    r = d[i:i + rs]
    code = struct.unpack_from('<H', r, 6)[0]
    if code <= prev and n > 5:
        break
    prev = code; n += 1; i += rs
print('records', n, 'end', hex(i), 'last code', hex(prev))
for k in list(range(0, 4)) + list(range(n - 3, n)):
    print(k, d[start + k * rs:start + (k + 1) * rs].hex())
