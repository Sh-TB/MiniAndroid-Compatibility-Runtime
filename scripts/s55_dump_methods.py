#!/usr/bin/env python3
# S55 R-NEW-361 recon: dump Lh/r;.c (ScatterMap findImpl) and LP/v$a;.c
# bytecode from dooz v18 — ground truth for the probe-arithmetic analysis.
import struct
import sys
import zipfile


def uleb(data, off):
    result = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, off


def parse(apk_path, want_classes):
    apk = zipfile.ZipFile(apk_path)
    data = apk.read('classes.dex')
    hdr = {
        'string_ids_size': struct.unpack_from('<I', data, 0x38)[0],
        'string_ids_off': struct.unpack_from('<I', data, 0x3C)[0],
        'type_ids_size': struct.unpack_from('<I', data, 0x40)[0],
        'type_ids_off': struct.unpack_from('<I', data, 0x44)[0],
        'proto_ids_off': struct.unpack_from('<I', data, 0x4C)[0],
        'field_ids_size': struct.unpack_from('<I', data, 0x50)[0],
        'field_ids_off': struct.unpack_from('<I', data, 0x54)[0],
        'method_ids_size': struct.unpack_from('<I', data, 0x58)[0],
        'method_ids_off': struct.unpack_from('<I', data, 0x5C)[0],
        'class_defs_size': struct.unpack_from('<I', data, 0x60)[0],
        'class_defs_off': struct.unpack_from('<I', data, 0x64)[0],
    }

    def get_str(idx):
        off = struct.unpack_from('<I', data, hdr['string_ids_off'] + idx * 4)[0]
        _, off = uleb(data, off)
        end = data.index(b'\x00', off)
        return data[off:end].decode('utf-8', errors='replace')

    def type_str(idx):
        sidx = struct.unpack_from('<I', data, hdr['type_ids_off'] + idx * 4)[0]
        return get_str(sidx)

    def method_ref(idx):
        off = hdr['method_ids_off'] + idx * 8
        cls_idx = struct.unpack_from('<H', data, off)[0]
        proto_idx = struct.unpack_from('<H', data, off + 2)[0]
        name_idx = struct.unpack_from('<I', data, off + 4)[0]
        return f"{type_str(cls_idx)}->{get_str(name_idx)}"

    def field_ref(idx):
        off = hdr['field_ids_off'] + idx * 8
        cls_idx = struct.unpack_from('<H', data, off)[0]
        type_idx = struct.unpack_from('<H', data, off + 2)[0]
        name_idx = struct.unpack_from('<I', data, off + 4)[0]
        return f"{type_str(cls_idx)}.{get_str(name_idx)}:{type_str(type_idx)}"

    out = {}
    for ci in range(hdr['class_defs_size']):
        cd = hdr['class_defs_off'] + ci * 32
        class_idx = struct.unpack_from('<I', data, cd)[0]
        cdesc = type_str(class_idx)
        if cdesc not in want_classes:
            continue
        class_data_off = struct.unpack_from('<I', data, cd + 24)[0]
        off = class_data_off
        static_fields, off = uleb(data, off)
        inst_fields, off = uleb(data, off)
        direct_methods, off = uleb(data, off)
        virtual_methods, off = uleb(data, off)
        # skip fields
        for _ in range(static_fields + inst_fields):
            _, off = uleb(data, off)
            _, off = uleb(data, off)
        methods = {}
        for _ in range(direct_methods + virtual_methods):
            mdiff, off = uleb(data, off)
            access, off = uleb(data, off)
            code_off, off = uleb(data, off)
            methods[mdiff] = (access, code_off)
        # method list is delta-encoded; walk all method_ids referenced
        # Instead: dump every method whose declaring class is this one via
        # method_ids scan (simple + complete).
        out[cdesc] = []
        for mi in range(hdr['method_ids_size']):
            offm = hdr['method_ids_off'] + mi * 8
            cls_idx = struct.unpack_from('<H', data, offm)[0]
            if type_str(cls_idx) != cdesc:
                continue
            name_idx = struct.unpack_from('<I', data, offm + 4)[0]
            mname = get_str(name_idx)
            # find code_off via the class_data diff table
            off = class_data_off
            _, off = uleb(data, off)
            _, off = uleb(data, off)
            dm, off = uleb(data, off)
            vm, off = uleb(data, off)
            for _ in range(dm + vm):
                _, off = uleb(data, off)
                _, off = uleb(data, off)
            acc_idx = 0
            midx = 0
            code_off = 0
            for k in range(dm + vm):
                mdiff, off = uleb(data, off)
                access, off = uleb(data, off)
                co, off = uleb(data, off)
                midx += mdiff
                # method_ids index of class methods are not sequential per
                # class necessarily; match by re-resolving name from the
                # method id list is unreliable here. Store all.
                methods[k] = (midx, co)
            # fallback: report offsets for all methods; caller matches by name
            out[cdesc].append((mname, methods))
        # simpler: for each method in the class_data, decode name from
        # method_ids by absolute index using the delta walk above (midx is
        # global method_ids index).
    return data, hdr, get_str, type_str, method_ref, field_ref, out


def dump_code(data, code_off, method_ref_fn, field_ref_fn, get_str, label):
    regs = struct.unpack_from('<H', data, code_off)[0]
    ins = struct.unpack_from('<H', data, code_off + 2)[0]
    outs = struct.unpack_from('<H', data, code_off + 4)[0]
    insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16
    print(f"\n## {label}: regs={regs} ins={ins} outs={outs} insns_size={insns_size} (16-bit units)")
    u16 = [struct.unpack_from('<H', data, insns_off + i * 2)[0] for i in range(insns_size)]
    pc = 0
    while pc < insns_size:
        w = u16[pc]
        op = w & 0xFF
        nx = lambda k: u16[pc + k] if pc + k < insns_size else 0
        line = f"pc={pc:4d} op=0x{op:02x}"
        if op in (0x54,):  # iget-object
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            fidx = nx(1)
            line += f" iget-object v{a}, v{b}, {field_ref_fn(fidx)}"
        elif op == 0x52:
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            fidx = nx(1)
            line += f" iget v{a}, v{b}, {field_ref_fn(fidx)}"
        elif op == 0x5b:
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            fidx = nx(1)
            line += f" iput-object v{a}, v{b}, {field_ref_fn(fidx)}"
        elif op == 0x59:
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            fidx = nx(1)
            line += f" iput v{a}, v{b}, {field_ref_fn(fidx)}"
        elif op in (0x6e, 0x6f, 0x70, 0x71):
            names = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super',
                     0x70: 'invoke-direct', 0x71: 'invoke-static'}
            midx = nx(1)
            line += f" {names[op]} {method_ref_fn(midx)}"
        elif op == 0x0e:
            line += " return-void"
        elif op == 0x11:
            line += " return-object"
        elif op == 0x0f:
            line += " return"
        elif op == 0x12:
            a = (w >> 8) & 0xF
            lit = (w >> 12) & 0xF
            if lit > 7:
                lit -= 16
            line += f" const/4 v{a}, #{lit}"
        elif op == 0x14:
            a = (w >> 8) & 0xF
            val = struct.unpack_from('<i', struct.pack('<H*'.replace('*', 'H') + 'HH', nx(1), nx(2), nx(3)), 0)[0] if False else \
                struct.unpack_from('<i', b''.join(struct.pack('<H', u16[pc + 1 + k]) for k in range(2)), 0)[0]
            line += f" const v{a}, #{val} (0x{val & 0xFFFFFFFF:08x})"
        elif op == 0x16:
            a = (w >> 8) & 0xF
            val = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" const-wide/16 v{a}, #{val}"
        elif op in (0xa1,):
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            line += f" ushr-long/2addr v{a}, v{b}"
        elif op == 0xbb:
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            line += f" sub-long/2addr v{a}, v{b}"
        elif op in range(0x44, 0x52):
            names = {0x44: 'aget', 0x45: 'aget-wide', 0x46: 'aget-object',
                     0x47: 'aget-boolean', 0x48: 'aget-byte',
                     0x4b: 'aput', 0x4c: 'aput-wide', 0x4d: 'aput-object',
                     0x4e: 'aput-boolean', 0x4f: 'aput-byte'}
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            c = nx(1) & 0xFF
            cc = (nx(1) >> 8) & 0xFF
            line += f" {names.get(op, f'array-0x{op:02x}')} v{a}, v{b}, v{c}|v{cc}"
        elif op == 0x21:
            a = (w >> 8) & 0xF
            b = (w >> 12) & 0xF
            line += f" array-length v{a}, v{b}"
        elif op in (0x33, 0x34, 0x35, 0x36, 0x32, 0x31):
            names = {0x31: 'if-eq', 0x32: 'if-ne', 0x33: 'if-lt',
                     0x34: 'if-ge', 0x35: 'if-gt', 0x36: 'if-le'}
            off = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" {names[op]} +{off} → {pc + off}"
        elif op in range(0x37, 0x3d):
            names = {0x37: 'if-eqz', 0x38: 'if-nez', 0x39: 'if-ltz',
                     0x3a: 'if-gez', 0x3b: 'if-gtz', 0x3c: 'if-lez'}
            off = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" {names[op]} +{off} → {pc + off}"
        elif op == 0x28:
            off = struct.unpack_from('<h', struct.pack('<H', nx(1)), 0)[0]
            line += f" goto/16 +{off} → {pc + off}"
        elif op == 0x27:
            line += " goto"
        elif op == 0x0b:
            line += " move-result-wide"
        elif op == 0x0c:
            line += " move-result-object"
        elif op == 0x0a:
            line += " move-result"
        elif op == 0xb0:
            line += " add-int/2addr"
        elif op == 0xa0:
            line += " add-long/2addr"
        elif op == 0x9d:
            line += " mul-int/2addr"
        elif op == 0xda:
            line += " rem-int/lit8?"
        elif op in (0xd7, 0xd8, 0xd5, 0xd6, 0xd3, 0xd4, 0xd1, 0xd2, 0xd0, 0xd1):
            line += f" binop/lit8-0x{op:02x}"
        elif op == 0x23:
            a = (w >> 8) & 0xF
            t = nx(1)
            line += f" new-array v{a}, tidx={t}"
        elif op == 0x22:
            t = nx(1)
            line += f" new-instance tidx={t}"
        elif op == 0x1c:
            t = nx(1)
            line += f" const-class tidx={t}"
        elif op == 0x71:
            pass
        else:
            line += f" ? (w=0x{w:04x})"
        print(line)
        # crude size advance: known 2-unit forms
        if op in (0x54, 0x52, 0x5b, 0x59, 0x6e, 0x6f, 0x70, 0x71, 0x14, 0x16,
                  0x23, 0x22, 0x1c, 0x28) or (0x31 <= op <= 0x3c) or op == 0x00 and False:
            if op == 0x14:
                pc += 3
            elif op == 0x16:
                pc += 2
            else:
                pc += 2
        else:
            pc += 1


if __name__ == '__main__':
    apk_path = sys.argv[1]
    data, hdr, get_str, type_str, method_ref, field_ref, out = parse(
        apk_path, {'Lh/r;', 'LP/v$a;', 'LP/v;'})
    # We dumped name maps per class; instead resolve each method's code via
    # the class_data delta walk + method_ids matching by name.
    for cdesc, entries in out.items():
        print(f"\n=== CLASS {cdesc} ===")
    # Simpler complete approach below: re-walk class_data per class with
    # absolute method index and decode each code item.
    class_defs_size = hdr['class_defs_size']
    class_defs_off = hdr['class_defs_off']

    def dump_class(cdesc):
        for ci in range(class_defs_size):
            cd = class_defs_off + ci * 32
            class_idx = struct.unpack_from('<I', data, cd)[0]
            if type_str(class_idx) != cdesc:
                continue
            class_data_off = struct.unpack_from('<I', data, cd + 24)[0]
            off = class_data_off
            sf, off = uleb(data, off)
            vf_n, off = uleb(data, off)
            dm, off = uleb(data, off)
            vm, off = uleb(data, off)
            for _ in range(sf + vf_n):
                _, off = uleb(data, off)
                _, off = uleb(data, off)
            midx = 0
            for k in range(dm + vm):
                if k == dm:
                    midx = 0  # virtual-method list restarts its delta run
                mdiff, off = uleb(data, off)
                access, off = uleb(data, off)
                code_off, off = uleb(data, off)
                midx += mdiff
                mname = method_ref(midx).split('->')[1].split('(')[0]
                if code_off == 0:
                    print(f"\n## {cdesc}->{mname}: abstract/native")
                    continue
                dump_code(data, code_off, method_ref, field_ref, get_str,
                          f"{cdesc}->{mname}")
            return

    dump_class('Lh/r;')
    dump_class('LP/v$a;')
