#!/usr/bin/env python3
"""Dump raw bytecode of a method from the blidraughts APK (ROOT-053 tool).
Usage: dump_blidraughts_method.py <class-Ldesc> <method> [descriptor-prefix]
"""
import sys, zipfile, struct

apk = '/tmp/s109_apks/blidraughts_3.apk'
target_class = sys.argv[1] if len(sys.argv) > 1 else 'Lcom/vovagorodok/blidraughts/MainActivity;'
target_method = sys.argv[2] if len(sys.argv) > 2 else 'getCurrentWebViewPackageInfo'
desc_prefix = sys.argv[3] if len(sys.argv) > 3 else ''

OPS_1 = {0x00:'nop',0x0e:'return-void',0x1d:'monitor-enter',0x1e:'monitor-exit',
         0x26:'throw',0x27:'goto'}
OPS_2 = {0x01:'move',0x04:'move-wide',0x07:'move-object',
         0x0a:'move-result',0x0b:'move-result-wide',0x0c:'move-result-object',
         0x0d:'move-exception',0x0f:'return',0x10:'return-wide',0x11:'return-object',
         0x12:'const/4',0x21:'array-length',0x13:'const/16',0x15:'const/high16',
         0x16:'const-wide/16',0x17:'const-wide/32',0x19:'const-wide/high16',
         0x1c:'const-class',0x1f:'check-cast',0x22:'new-instance',0x28:'goto/16',
         0x37:'if-eqz',0x38:'if-nez',0x39:'if-ltz',0x3a:'if-gez',0x3b:'if-gtz',
         0x3c:'if-lez',0x20:'instance-of',0x23:'new-array',0x31:'if-eq',0x32:'if-ne',
         0x33:'if-lt',0x34:'if-ge',0x35:'if-gt',0x36:'if-le',
         0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
         0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',
         0x59:'iput',0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',
         0x5d:'iput-byte',0x5e:'iput-short',0x5f:'iput-char',
         0x62:'sget',0x63:'sget-wide',0x64:'sget-object',0x65:'sget-boolean',
         0x66:'sget-byte',0x67:'sget-char',0x68:'sget-short',
         0x69:'sput',0x6a:'sput-wide',0x6b:'sput-object',0x6c:'sput-boolean',
         0x6e:'invoke-virtual',0x6f:'invoke-super',0x70:'invoke-direct',
         0x71:'invoke-static',0x72:'invoke-interface',
         0x1a:'const-string',0x1b:'const-string/jumbo',
         0x29:'goto/32',0x2b:'packed-switch',0x2c:'sparse-switch'}
INVOKE = {0x6e,0x6f,0x70,0x71,0x72}

def u2(b,o): return struct.unpack_from('<H',b,o)[0]
def u4(b,o): return struct.unpack_from('<I',b,o)[0]

z = zipfile.ZipFile(apk)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print('dex files:', dex_names)

for dn in dex_names:
    d = z.read(dn)
    # header
    string_ids_size, string_ids_off = u4(d,56), u4(d,60)
    type_ids_size, type_ids_off = u4(d,64), u4(d,68)
    proto_ids_size, proto_ids_off = u4(d,72), u4(d,76)
    field_ids_size, field_ids_off = u4(d,80), u4(d,84)
    method_ids_size, method_ids_off = u4(d,88), u4(d,92)
    class_ids_size, class_ids_off = u4(d,96), u4(d,100)

    def get_string(idx):
        off = u4(d, string_ids_off + 4*idx)
        # uleb128 length
        r = off; shift=0; size=0
        while True:
            b_ = d[r]; r += 1
            size |= (b_ & 0x7f) << shift
            if not (b_ & 0x80): break
            shift += 7
        return d[r:r+size].decode('utf-8', errors='replace')

    def get_type(idx):
        return get_string(u4(d, type_ids_off + 4*idx))

    def get_method(idx):
        moff = method_ids_off + 8*idx
        cls_idx = u2(d, moff); proto_idx = u2(d, moff+2); name_idx = u4(d, moff+4)
        return get_type(cls_idx), get_string(name_idx), proto_idx

    # find class_def
    for ci in range(class_ids_size):
        cdo = class_ids_off + 32*ci
        cls_idx = u4(d, cdo)
        cls_desc = get_type(cls_idx)
        if cls_desc != target_class: continue
        class_data_off = u4(d, cdo + 24)
        if not class_data_off: print('no class data'); continue
        o = [class_data_off]
        def uleb():
            r=0; shift=0
            while True:
                b_ = d[o[0]]; o[0] += 1
                r |= (b_ & 0x7f) << shift
                if not (b_ & 0x80): break
                shift += 7
            return r
        static_fields = uleb(); inst_fields = uleb()
        direct_methods = uleb(); virtual_methods = uleb()
        # skip fields
        for _ in range(static_fields):
            uleb(); uleb()
        for _ in range(inst_fields):
            uleb(); uleb()
        for kind,cnt in (('direct',direct_methods),('virtual',virtual_methods)):
            midx = 0
            for _ in range(cnt):
                d_idx = midx + uleb(); midx = d_idx
                access = uleb(); code_off = uleb()
                mcls, mname, mproto = get_method(d_idx)
                if mname != target_method: continue
                print(f'== {kind} {cls_desc}.{mname} code_off=0x{code_off:x}')
                if not code_off: print('  (abstract/native)'); continue
                co = code_off
                regs = u2(d,co); ins = u2(d,co+2); outs = u2(d,co+4)
                insns_size = u4(d, co+12); insns_off = co+16
                print(f'  regs={regs} ins={ins} outs={outs} insns={insns_size}')
                p = insns_off; end = insns_off + insns_size*2
                while p < end:
                    w = u2(d,p)
                    op = w & 0xff
                    name = OPS_1.get(op) or OPS_2.get(op, f'op_{op:02x}')
                    if op in INVOKE or op in (0x62,0x63,0x64,0x65,0x66,0x67,0x68,
                                              0x69,0x6a,0x6b,0x6c,0x52,0x53,0x54,
                                              0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,
                                              0x5c,0x5d,0x5e,0x5f,0x1a,0x1f,0x22,
                                              0x6d):
                        idx = u2(d,p+2)
                        if op in INVOKE:
                            mc,mn,mp = get_method(idx)
                            print(f'  {p-insns_off:04x}: {name} {mc}.{mn}')
                        elif op == 0x1a:
                            print(f'  {p-insns_off:04x}: const-string "{get_string(idx)}"')
                        else:
                            try: print(f'  {p-insns_off:04x}: {name} @{get_type(idx)}')
                            except Exception: print(f'  {p-insns_off:04x}: {name} @{idx}')
                        p += 4
                    elif op == 0x12:
                        print(f'  {p-insns_off:04x}: const/4 v{w>>8&0xf}, {(w>>12)&0xf}')
                        p += 2
                    else:
                        print(f'  {p-insns_off:04x}: {name}')
                        p += 2
