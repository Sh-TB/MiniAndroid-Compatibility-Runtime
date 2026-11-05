#!/usr/bin/env python3
"""s169_disasm.py — S169: signature-aware DEX disassembly for the W8
Room-storage chain. Finds which DBUtil outline overload carries the
"Storage database upgrade failed!" const-string, then dumps it +
K9StoragePersister.openDB."""
import struct
import sys
import zipfile

sys.path.insert(0, '/home/z/my-project/scripts')
from cont9_dexdump import Dex

# opcode -> (byte-size, format, name) — format-based size law
OPS = {}


def _r(a, b, size, fmt, name):
    for o in range(a, b + 1):
        OPS[o] = (size, fmt, name)


_r(0x00, 0x00, 2, '10x', 'nop'); _r(0x01, 0x01, 2, '12x', 'move')
_r(0x02, 0x02, 4, '22x', 'move/from16'); _r(0x03, 0x03, 6, '32x', 'move/16')
_r(0x04, 0x04, 2, '12x', 'move-wide')
_r(0x05, 0x05, 4, '22x', 'move-wide/from16')
_r(0x06, 0x06, 6, '32x', 'move-wide/16')
_r(0x07, 0x07, 2, '12x', 'move-object')
_r(0x08, 0x08, 4, '22x', 'move-object/from16')
_r(0x09, 0x09, 6, '32x', 'move-object/16')
_r(0x0a, 0x0d, 2, '11x', 'move-result*')
_r(0x0e, 0x0e, 2, '10x', 'return-void'); _r(0x0f, 0x11, 2, '11x', 'return*')
_r(0x12, 0x12, 2, '11n', 'const/4'); _r(0x13, 0x13, 4, '21s', 'const/16')
_r(0x14, 0x14, 6, '31i', 'const'); _r(0x15, 0x15, 4, '21h', 'const/high16')
_r(0x16, 0x16, 4, '21s', 'const-wide/16')
_r(0x17, 0x17, 6, '31i', 'const-wide/32')
_r(0x18, 0x18, 10, '51l', 'const-wide')
_r(0x19, 0x19, 4, '21h', 'const-wide/high16')
_r(0x1a, 0x1a, 4, '21c', 'const-string')
_r(0x1b, 0x1b, 6, '31c', 'const-string/jumbo')
_r(0x1c, 0x1c, 4, '21c', 'const-class')
_r(0x1d, 0x1e, 2, '11x', 'monitor*'); _r(0x1f, 0x1f, 4, '21c', 'check-cast')
_r(0x20, 0x20, 4, '22c', 'instance-of')
_r(0x21, 0x21, 2, '12x', 'array-length')
_r(0x22, 0x22, 4, '21c', 'new-instance')
_r(0x23, 0x23, 4, '22c', 'new-array')
_r(0x24, 0x24, 6, '35c', 'filled-new-array')
_r(0x25, 0x25, 6, '3rc', 'filled-new-array/range')
_r(0x26, 0x26, 6, '31t', 'fill-array-data'); _r(0x27, 0x27, 2, '11x', 'throw')
_r(0x28, 0x28, 2, '10t', 'goto'); _r(0x29, 0x29, 4, '20t', 'goto/16')
_r(0x2a, 0x2a, 10, '30t', 'goto/32'); _r(0x2b, 0x2c, 6, '31t', '*-switch')
_r(0x2d, 0x31, 4, '23x', 'cmp*'); _r(0x32, 0x37, 4, '22t', 'if-*')
_r(0x38, 0x3d, 4, '21t', 'if-*z'); _r(0x3e, 0x43, 2, '10x', 'unused')
_r(0x44, 0x51, 4, '23x', 'a*get/put'); _r(0x52, 0x5f, 4, '22c', 'i*get/put')
_r(0x60, 0x6d, 4, '21c', 's*get/put'); _r(0x6e, 0x72, 6, '35c', 'invoke-*')
_r(0x73, 0x73, 2, '10x', 'unused'); _r(0x74, 0x78, 6, '3rc', 'invoke-*/range')
_r(0x79, 0x7a, 2, '10x', 'unused'); _r(0x7b, 0x8f, 2, '12x', 'unary-op')
_r(0x90, 0xaf, 4, '23x', 'binop'); _r(0xb0, 0xcf, 2, '12x', 'binop/2addr')
_r(0xd0, 0xe5, 4, '22b', 'binop/lit8'); _r(0xe6, 0xf9, 4, '22s', 'binop/lit16')
_r(0xfa, 0xfa, 8, '45cc', 'invoke-polymorphic')
_r(0xfb, 0xfb, 8, '4rcc', 'invoke-polymorphic/range')
_r(0xfc, 0xfd, 4, '21c', 'const-method-*/'); _r(0xfe, 0xff, 2, '10x', 'unused')


def opname(op):
    return OPS[op][2] if op in OPS else f'op-{op:02x}'

APK = '/home/z/my-project/upload/net.thunderbird.android_33.apk'


def disasm(d, dex_bytes, cls, mname, mdesc_want=None, max_units=None):
    cdef = d.find_class(cls)
    if cdef is None:
        print('class not found:', cls)
        return
    info = d.class_methods(cdef)
    hits = []
    for kind in ('direct', 'virtual'):
        for (mn, md, acc, sz, code) in info[kind]:
            if mn == mname and (mdesc_want is None or mdesc_want in md):
                hits.append((md, sz, code))
    for md, sz, code in hits:
        insns_size = struct.unpack_from('<I', dex_bytes, code + 12)[0]
        off = code + 16
        print(f"{cls}.{mname}{md} code_off=0x{code:x} "
              f"insns={insns_size} units")

        def fstr(idx):
            try:
                return "%s.%s:%s" % d.field_ref(idx)
            except Exception:
                return f"field@{idx}"

        def mstr(idx):
            try:
                return "%s.%s%s" % d.method_ref(idx)
            except Exception:
                return f"method@{idx}"

        pc = 0
        end = insns_size * 2
        buf = dex_bytes
        while pc < end:
            op = buf[off + pc]
            size, fmt, _ = OPS.get(op, (2, '??', '?'))
            detail = ''
            try:
                if fmt == '21t':
                    reg = buf[off + pc + 1]
                    o = struct.unpack_from('<h', buf, off + pc + 2)[0]
                    detail = f"v{reg} -> 0x{pc + o*2:x}"
                elif fmt == '10t':
                    o = struct.unpack_from('<b', buf, off + pc + 1)[0]
                    detail = f"-> 0x{pc + o*2:x}"
                elif fmt == '21c':
                    reg = buf[off + pc + 1]
                    idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                    detail = f"v{reg}, @{(mstr if op in (0x1a,0x1b) else fstr)(idx)}"
                    if op in (0x1a, 0x1b):
                        try:
                            detail = f'v{reg}, "{d.string_ref(idx)}"'
                        except Exception:
                            pass
                elif fmt == '31c':
                    reg = buf[off + pc + 1]
                    idx = struct.unpack_from('<I', buf, off + pc + 2)[0]
                    try:
                        detail = f'v{reg}, "{d.string_ref(idx)}"'
                    except Exception:
                        detail = f"v{reg}, str@{idx}"
                elif fmt == '22c':
                    ra = buf[off + pc + 1] & 0xF
                    rb = buf[off + pc + 1] >> 4
                    idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                    detail = f"v{ra}, v{rb}, @{fstr(idx)}"
                elif fmt == '35c':
                    idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                    regs = buf[off + pc + 4:off + pc + 6]
                    rl = [f"v{b & 0xF if i == 0 else b >> 4}"
                          for i, b in enumerate(regs)]
                    detail = f"{','.join(rl)}, @{mstr(idx)}"
                elif fmt == '3rc':
                    idx = struct.unpack_from('<H', buf, off + pc + 2)[0]
                    ra = buf[off + pc + 4]
                    cnt = buf[off + pc + 5]
                    detail = (f"v{ra}..v{ra+cnt-1}"
                              if cnt else f"v{ra}), @{mstr(idx)}")
                elif fmt == '10x':
                    pass
                elif fmt == '11x':
                    detail = f"v{buf[off+pc+1]}"
                elif fmt == '11n':
                    r = buf[off + pc + 1] & 0xF
                    lit = buf[off + pc + 1] >> 4
                    detail = f"v{r}, {lit - 16 if lit > 7 else lit}"
                elif fmt == '22b':
                    ra = buf[off + pc + 1]
                    rb = buf[off + pc + 2]
                    lit = struct.unpack_from('<b', buf, off + pc + 3)[0]
                    detail = f"v{ra}, v{rb}, {lit}"
                elif fmt == '31i':
                    reg = buf[off + pc + 1]
                    lit = struct.unpack_from('<i', buf, off + pc + 2)[0]
                    detail = f"v{reg}, {lit}"
            except Exception as e:
                detail = f"(decode err {e})"
            print(f"  0x{pc:04x}: {opname(op):<26} {detail}")
            pc += size
        print()


def main():
    z = zipfile.ZipFile(APK)
    dex_names = sorted(n for n in z.namelist()
                       if n.startswith('classes') and n.endswith('.dex'))
    # 1) find the DBUtil outline overload carrying the upgrade-failed string
    for dname in dex_names:
        dex_bytes = z.read(dname)
        d = Dex(dex_bytes)
        cdef = d.find_class(
            'Landroidx/room/util/DBUtil$$ExternalSyntheticBUOutline0;')
        if cdef is None:
            continue
        info = d.class_methods(cdef)
        for kind in ('direct', 'virtual'):
            for (mn, md, acc, sz, code) in info[kind]:
                if mn != 'm':
                    continue
                insns_size = struct.unpack_from('<I', dex_bytes,
                                                code + 12)[0]
                blob = dex_bytes[code + 16:code + 16 + insns_size * 2]
                if b'Storage database upgrade failed' in blob:
                    print(f"[FOUND] {dname} m{md} "
                          f"carries the upgrade-failed string")
                    disasm(d, dex_bytes,
                           'Landroidx/room/util/DBUtil$$ExternalSynthetic'
                           'BUOutline0;', 'm', md)
    # 2) K9StoragePersister.openDB
    for dname in dex_names:
        dex_bytes = z.read(dname)
        d = Dex(dex_bytes)
        cdef = d.find_class('Lcom/fsck/k9/preferences/K9StoragePersister;')
        if cdef is None:
            continue
        disasm(d, dex_bytes, 'Lcom/fsck/k9/preferences/K9StoragePersister;',
               'openDB')
        break


if __name__ == '__main__':
    main()
