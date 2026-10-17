import struct, sys, re
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

BOOT = 'work/iso/PSP_GAME/SYSDIR/BOOT.BIN'


class Elf:
    def __init__(self, path=BOOT):
        self.d = open(path, 'rb').read()
        d = self.d
        phoff, = struct.unpack_from('<I', d, 0x1c)
        phnum, = struct.unpack_from('<H', d, 0x2c)
        self.segs = []
        for i in range(phnum):
            t, off, va, pa, fs, ms, fl, al = struct.unpack_from('<8I', d, phoff + 32 * i)
            if t == 1:
                self.segs.append((va, off, fs, ms))
        self.md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)

    def v2o(self, va):
        for v, o, fs, ms in self.segs:
            if v <= va < v + fs: return o + va - v
    def o2v(self, off):
        for v, o, fs, ms in self.segs:
            if o <= off < o + fs: return v + off - o

    def dis(self, va, n):
        o = self.v2o(va)
        out = []
        for ins in self.md.disasm(self.d[o:o + 4 * n], va):
            out.append('%08x: %s %s' % (ins.address, ins.mnemonic, ins.op_str))
        return out

    def xrefs(self, target):
        """find lui/addiu(ori) pairs building target address"""
        hi = (target + 0x8000) >> 16; lo = target & 0xffff
        res = []
        v, o, fs, ms = self.segs[0]
        for i in range(0, fs, 4):
            w, = struct.unpack_from('<I', self.d, o + i)
            if w >> 26 == 0xf and (w & 0xffff) == hi:
                rt = (w >> 16) & 31
                for j in range(1, 40):
                    w2, = struct.unpack_from('<I', self.d, o + i + 4 * j)
                    op = w2 >> 26
                    if op in (9, 0xd, 0x23, 0x21, 0x25, 0x24, 0x2b, 0x29, 0x28) and ((w2 >> 21) & 31) == rt and (w2 & 0xffff) == lo:
                        res.append(v + i + 4 * j); break
        return res


if __name__ == '__main__':
    e = Elf()
    print([(hex(a), hex(b), hex(c)) for a, b, c, _ in e.segs])
    if sys.argv[1] == 'x':
        t = int(sys.argv[2], 0)
        if len(sys.argv) > 3 and sys.argv[3] == 'off': t = e.o2v(t)
        for a in e.xrefs(t): print(hex(a))
    elif sys.argv[1] == 'd':
        print('\n'.join(e.dis(int(sys.argv[2], 0), int(sys.argv[3]))))
