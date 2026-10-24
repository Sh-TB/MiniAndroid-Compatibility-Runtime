#!/usr/bin/env python3
"""cont28_dooz_gq0_truth.py — DEX truth for dooz S102 face:
(1) does classes.dex carry a class_def for Landroidx/compose/ui/platform/AndroidCompositionLocals_androidKt; ?
(2) disassemble Lgq0;.<clinit> pc=14 area to see the exact CNF trigger.
Pure-python DEX parsing (no androguard needed).
"""
import struct, sys, zipfile

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
TARGET = "Landroidx/compose/ui/platform/AndroidCompositionLocals_androidKt;"
GQ0 = "Lgq0;"

z = zipfile.ZipFile(APK)
data = z.read("classes.dex")

def u4(off): return struct.unpack_from("<I", data, off)[0]
def u2(off): return struct.unpack_from("<H", data, off)[0]

# header
string_ids_size, string_ids_off = struct.unpack_from("<II", data, 0x38)
type_ids_size, type_ids_off = struct.unpack_from("<II", data, 0x40)
proto_ids_size, proto_ids_off = struct.unpack_from("<II", data, 0x48)
field_ids_size, field_ids_off = struct.unpack_from("<II", data, 0x50)
method_ids_size, method_ids_off = struct.unpack_from("<II", data, 0x58)
class_defs_size, class_defs_off = struct.unpack_from("<II", data, 0x60)
print(f"dex: strings={string_ids_size} types={type_ids_size} methods={method_ids_size} classes={class_defs_size}")

def get_string(idx):
    off = u4(string_ids_off + 4*idx)
    # MUTF-8: skip uleb128 length
    p = off
    b = 0; shift = 0; ln = 0
    while True:
        b = data[p]; p += 1
        ln |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80): break
    end = data.find(b"\x00", p)
    return data[p:end].decode("utf-8", "replace")

# string lookup: build map of target strings
want_str_idx = None
for i in range(string_ids_size):
    s = get_string(i)
    if TARGET in s:
        want_str_idx = i
        print(f"string[{i}] = {s!r}")
        break

# type id for target
target_type_idx = None
if want_str_idx is not None:
    for t in range(type_ids_size):
        if u4(type_ids_off + 4*t) == want_str_idx:
            target_type_idx = t
            print(f"type_idx = {t}")
            break

# class_def scan: is the target a DEFINED class?
defined = False
for c in range(class_defs_size):
    off = class_defs_off + 32*c
    class_idx = u4(off)
    if class_idx == target_type_idx:
        defined = True
        print(f"CLASS_DEF EXISTS: class[{c}] access=0x{u4(off+4):x} superclass_idx={u4(off+8)}")
        break
if not defined:
    print("NO CLASS_DEF for target — string is only a Class.forName constant (R8 keep-name)")

# disassemble Lgq0;.<clinit>
def get_type_str(idx):
    return get_string(u4(type_ids_off + 4*idx))

def find_method(cls_desc, name):
    for m in range(method_ids_size):
        off = method_ids_off + 8*m
        cls_t = u2(off); name_s = u4(off+4)  # proto_idx at +2
        if get_type_str(cls_t) == cls_desc and get_string(name_s) == name:
            return m
    return None

gq0_cls = None
for c in range(class_defs_size):
    off = class_defs_off + 32*c
    if get_type_str(u4(off)) == GQ0:
        gq0_cls = off
        break
if gq0_cls is None:
    print("Lgq0; NOT FOUND in class_defs")
    sys.exit(0)

class_data_off = u4(gq0_cls + 24)
print(f"Lgq0; class_data_off=0x{class_data_off:x}")
if class_data_off == 0:
    print("no class data")
    sys.exit(0)

p = class_data_off
def uleb(p):
    r=0; s=0
    while True:
        b=data[p]; p+=1; r|=(b&0x7F)<<s; s+=7
        if not (b&0x80): break
    return r,p

static_fields_size, p = uleb(p)
instance_fields_size, p = uleb(p)
direct_methods_size, p = uleb(p)
virtual_methods_size, p = uleb(p)
# skip fields
for _ in range(static_fields_size):
    _, p = uleb(p); _, p = uleb(p)
for _ in range(instance_fields_size):
    _, p = uleb(p); _, p = uleb(p)

def read_methods(p, count):
    idx = 0
    out = []
    for _ in range(count):
        diff, p = uleb(p)
        access, p = uleb(p)
        code_off, p = uleb(p)
        idx += diff
        out.append((idx, access, code_off))
    return out, p

directs, p = read_methods(p, direct_methods_size)
virtuals, p = read_methods(p, virtual_methods_size)

clinit_code = None
for midx, access, code_off in directs + virtuals:
    name = get_string(u4(method_ids_off + 8*midx + 4))
    if name == "<clinit>" and code_off:
        clinit_code = code_off
print(f"<clinit> code_off=0x{clinit_code:x}" if clinit_code else "<clinit> has NO code")

if clinit_code:
    registers_size, ins_size, outs_size, tries_size, debug_info_off, insns_size = struct.unpack_from("<HHHHII", data, clinit_code)
    insns = clinit_code + 16
    print(f"registers={registers_size} insns_size={insns_size} code units")
    # decode first ~30 instructions (16-bit words), annotate common opcodes
    names = {0x0b:"move-result",0x0c:"move-result-wide",0x0a:"move-result-object",
             0x12:"const/4",0x13:"const/16",0x14:"const",0x1a:"const-string",
             0x71:"invoke-static",0x6e:"invoke-virtual",0x70:"invoke-direct",
             0x62:"sget-object",0x6b:"sput-object",0x54:"iget-object",0x59:"iput-object",
             0x22:"new-instance",0x23:"new-array",0x27:"throw",0x11:"move-object",
             0x0e:"return-void",0x0f:"return",0x10:"return-object"}
    for pc in range(0, min(60, insns_size)):
        w = u2(insns + 2*pc)
        op = w & 0xFF
        nm = names.get(op)
        if nm in ("const-string",):
            sidx = u2(insns + 2*(pc+1))
            print(f"  pc={pc:#04x} const-string v{((w>>8)&0xF)}, '{get_string(sidx)[:70]}'")
            pc += 1
        elif nm in ("invoke-static",):
            mid = u2(insns + 2*(pc+1))
            mname = get_string(u4(method_ids_off + 8*mid + 4))
            mcls = get_type_str(u2(method_ids_off + 8*mid))
            print(f"  pc={pc:#04x} invoke-static {mcls}.{mname}")
            pc += 2
        elif nm:
            print(f"  pc={pc:#04x} {nm} (w={w:#06x})")
    # exact pc=14 word
    w14 = u2(insns + 2*14)
    op14 = w14 & 0xFF
    print(f"pc=14 word={w14:#06x} op={op14:#04x} {names.get(op14,'?')}")
    if op14 == 0x1a:
        sidx = u2(insns + 2*15)
        print(f"  -> const-string '{get_string(sidx)}'")
