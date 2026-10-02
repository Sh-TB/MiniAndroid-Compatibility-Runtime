#!/usr/bin/env python3
"""F-NEW-197: precise disassembly of SlidingUpPanelLayout.<init> around the
gravity read — full opcode-width walk (ground truth for defValue + styleable)."""
import struct, zipfile

APK = '/home/z/my-project/upload/opencalculator_53.apk'
TARGET = 'Lcom/sothree/slidinguppanel/SlidingUpPanelLayout;'
LO, HI = 0x3f, 0xa1   # instruction window (code units) around the gravity read

# canonical dalvik instruction widths (in 16-bit code units)
def opwidth(op):
    if op in (0x00,): return 1                    # nop
    if op in (0x01,0x04,0x07,0x0a,0x0d,0x0e,0x11,0x12,0x15,0x16,0x1c,0x1d,
              0x1f,0x20,0x21,0x22,0x23,0x27,0x28,0x29,0x0b,0x0c,0x03): return 1
    if op in (0x02,0x05,0x08,0x0f,0x10,0x13,0x14,0x17,0x18,0x19,0x1a,0x1b,
              0x1e,0x24,0x25,0x26,0x2b,0x2c,0x6b,0x6c,0x6d,0x5f,0x62,0x65,
              0x68): return 2
    if 0x30 <= op <= 0x3d: return 2               # if/cmp
    if 0x44 <= op <= 0x51: return 2               # aget/aput
    if 0x52 <= op <= 0x6a: return 2               # iget/iput/sget/sput 22c/21c
    if 0x6e <= op <= 0x72: return 3               # invoke 35c
    if 0x74 <= op <= 0x78: return 3               # invoke range
    if op in (0x14,0x17): return 2
    if op == 0x16: return 1
    if op in (0x18,): return 3                    # const-wide/16? (0x16=1,0x17=2,0x18=3)
    if op in (0x19,): return 1
    if op in (0x13,): return 2
    if op in (0x15,): return 2
    if op in (0xa0,0xa1,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xab,
              0xac,0xad,0xae,0xaf,0xb0,0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,
              0xb8,0xb9,0xba,0xbb,0xbc,0xbd,0xbe,0xbf,0xc0,0xc1,0xc2,0xc3,
              0xc4,0xc5,0xc6,0xc7,0xc8,0xc9,0xca,0xcb,0xcc,0xcd,0xce,0xcf,
              0xd0,0xd1,0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,0xd8,0xd9,0xda,0xdb,
              0xdc,0xdd,0xde,0xdf,0xe0,0xe1,0xe2,0xe3,0xe4,0xe5,0xe6,0xe7,
              0xe8,0xe9,0xea,0xeb,0xec,0xed,0xee,0xef,0xf0,0xf1,0xf2,0xf3,
              0xf4,0xf5,0xf6,0xf7,0xf8,0xf9): return 1
    if op in (0xfa,0xfb,0xfc,0xfd): return 4      # invoke-polymorphic/custom
    if op in (0x2a,0x2b,0x2c): return 3           # packed/sparse-switch
    if op == 0x29: return 2
    if op == 0x28: return 1
    if op in (0x2d,0x2e,0x2f,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,
              0x3b,0x3c,0x3d): return 2
    if op in (0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x8b,0x8c,
              0x8d,0x8e,0x8f): return 1
    return 1

NAMES = {0x12:'const/4',0x13:'const/16',0x14:'const',0x15:'const/high16',
         0x1a:'const-string',0x1b:'const-string/jumbo',0x1c:'const-class',
         0x22:'new-instance',0x23:'new-array',0x24:'filled-new-array',
         0x54:'iget',0x55:'iget-wide',0x56:'iget-object',0x57:'iget-boolean',
         0x5a:'iput',0x5c:'sget',0x5e:'sget-object',0x5f:'sget-boolean',
         0x62:'sget-object2',0x60:'sget',0x61:'sget-wide',0x63:'sget-object',
         0x69:'sput-object',0x6e:'invoke-virtual',0x6f:'invoke-super',
         0x70:'invoke-direct',0x71:'invoke-static',0x72:'invoke-interface',
         0x74:'invoke-virtual/range',0x77:'invoke-static/range',
         0x0a:'move-result',0x0c:'move-result-object',0x0b:'move-result-wide',
         0x21:'instance-of',0x20:'check-cast',0x27:'throw',0x28:'goto',
         0x29:'goto/16',0x2a:'goto/32'}

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

def main():
    z = zipfile.ZipFile(APK)
    for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        d = z.read(name)
        ssz, soff = struct.unpack_from('<II', d, 0x38)
        strs = []
        for i in range(ssz):
            so = struct.unpack_from('<I', d, soff + i*4)[0]
            ln, doff = uleb(d, so)
            strs.append(d[doff:doff+ln*4].decode('utf-8', errors='replace').split('\x00')[0])
        tsz, toff = struct.unpack_from('<II', d, 0x40)
        types = [strs[struct.unpack_from('<I', d, toff + i*4)[0]] for i in range(tsz)]
        msz, moff = struct.unpack_from('<II', d, 0x58)
        methods = []
        for i in range(msz):
            cls, proto, nm = struct.unpack_from('<HHI', d, moff + i*8)
            methods.append((types[cls], strs[nm]))
        fsz, foff = struct.unpack_from('<II', d, 0x50)
        fields = []
        for i in range(fsz):
            cls, typ, nm = struct.unpack_from('<HHI', d, foff + i*8)
            fields.append((types[cls], types[typ], strs[nm]))
        # class def
        cdsz, cdoff = struct.unpack_from('<II', d, 0x60)
        cdo = None
        for i in range(cdsz):
            cd = cdoff + i*32
            cls_idx = struct.unpack_from('<I', d, cd)[0]
            if types[cls_idx] == TARGET:
                cdo = struct.unpack_from('<I', d, cd + 24)[0]
                break
        if cdo is None: continue
        print('FOUND', name)
        off = cdo
        sf, off = uleb(d, off); inf, off = uleb(d, off); dm, off = uleb(d, off); vm, off = uleb(d, off)
        for _ in range(sf + inf):
            _, off = uleb(d, off); _, off = uleb(d, off)
        midx = 0
        for _ in range(dm + vm):
            dlt, off = uleb(d, off); midx += dlt
            acc, off = uleb(d, off); co, off = uleb(d, off)
            cls, nm = methods[midx]
            if nm not in ("<init>", "<clinit>"): continue
            print(f'=== <init> code_off={co:#x} ===')
            if co == 0: continue
            reg, ins, outs = struct.unpack_from('<HHH', d, co + 4)
            insns_size, = struct.unpack_from('<I', d, co + 0x0c)
            base = co + 0x10
            pc = 0
            while pc < insns_size:
                if not (LO <= pc <= HI):
                    pc += opwidth(d[base + pc*2] & 0xff)
                    continue
                op = d[base + pc*2] & 0xff
                w = struct.unpack_from('<H', d, base + pc*2)[0]
                ann = NAMES.get(op, f'op{op:#04x}')
                extra = ''
                if op in (0x6e,0x6f,0x70,0x71,0x72):
                    midx2 = struct.unpack_from('<H', d, base + pc*2 + 2)[0]
                    extra = f' {methods[midx2][0]}->{methods[midx2][1]}'
                    # format35c: A|G|op BBBB F|E|D|C — arg order C,D,E,F,G
                    regword = struct.unpack_from('<H', d, base + pc*2 + 4)[0]
                    gs = [regword & 0xf, (regword >> 4) & 0xf,
                          (regword >> 8) & 0xf, (regword >> 12) & 0xf,
                          (w >> 8) & 0xf]
                    cnt = (w >> 12) & 0xf
                    extra += f'  vregs={[gs[i] for i in range(min(cnt,4))]}'
                elif op == 0x12:
                    extra = f' v{(w>>8)&0xf} = {(w>>12)&0xf}'
                    if (w>>12)&0x8: extra += f' (signed={((w>>12)&0xf)-16})'
                elif op == 0x13:
                    v = struct.unpack_from('<h', d, base + pc*2 + 2)[0]
                    extra = f' v{(w>>8)&0xff} = {v}'
                elif op == 0x14:
                    v = struct.unpack_from('<i', d, base + pc*2 + 2)[0]
                    extra = f' v{(w>>8)&0xff} = {v} ({v:#x})'
                elif op == 0x15:
                    v = struct.unpack_from('<H', d, base + pc*2 + 2)[0] << 16
                    extra = f' v{(w>>8)&0xff} = {v} ({v:#x})'
                elif 0x52 <= op <= 0x6a:
                    fidx = struct.unpack_from('<H', d, base + pc*2 + 2)[0]
                    extra = f' v{(w>>8)&0xff} <- {fields[fidx][0]}.{fields[fidx][2]}:{fields[fidx][1]}'
                elif op in (0x0a,0x0b,0x0c,0x0d):  # move-result family
                    extra = f' v{(w>>8)&0xff}'
                elif op in (0x01,0x04,0x07):       # move / move-wide / move-object
                    extra = f' v{(w>>8)&0xff} <- v{(w>>12)&0xf}'
                elif op in (0x02,0x05,0x08):       # move/from16 family
                    src = struct.unpack_from('<H', d, base + pc*2 + 2)[0]
                    extra = f' v{(w>>8)&0xff} <- v{src>>8}'
                print(f'  +{pc:#06x} {ann}{extra}')
                pc += opwidth(op)
            print('  (end of method)')

if __name__ == '__main__':
    main()
