#!/usr/bin/env python3.13
# cont33_jvm_disasm.py — decode canBeSavedToBundle from ui-android 1.11.4 AAR
# (JVM class files; androguard 4.x dropped its JVM module so we walk raw
# bytecode with a compact opcode table). Goal: the EXACT canBeSaved predicate
# ART runs, to verdict the UUID rememberSaveable IAE (faithful vs engine gap).
import struct, sys

path = sys.argv[1]
target = sys.argv[2] if len(sys.argv) > 2 else "canBeSavedToBundle"
b = open(path, "rb").read()

# --- constant pool ---
n = struct.unpack(">H", b[8:10])[0]
i, cp, count = 10, {}, 1
while count < n:
    tag = b[i]
    if tag == 1:
        ln = struct.unpack(">H", b[i+1:i+3])[0]
        cp[count] = ("utf8", b[i+3:i+3+ln].decode("utf8", "replace")); i += 3 + ln
    elif tag in (7, 8, 16, 19, 20):
        cp[count] = ("i", struct.unpack(">H", b[i+1:i+3])[0]); i += 3
    elif tag == 15:
        cp[count] = ("m", b[i+1:i+4]); i += 4
    elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
        cp[count] = ("ii", struct.unpack(">HH", b[i+1:i+5])); i += 5
    elif tag in (5, 6):
        cp[count] = ("l", b[i+1:i+9]); i += 9; count += 1
    else:
        raise Exception(f"tag {tag} at {i}")
    count += 1

def utf(idx): return cp[idx][1]
def ci(idx):
    t = cp[idx]
    if t[0] == "ii":
        name, desc = utf(t[1][0]), utf(t[1][1])
        return name
    if t[0] == "i": return utf(t[1])
    return str(t)

# --- class structure: skip to fields/methods ---
acc, this_c, super_c = struct.unpack(">HHH", b[i:i+6]); i += 6

ifs = struct.unpack(">H", b[i:i+2])[0]; i += 2 + 2 * ifs
def skip_attrs(i):
    na = struct.unpack(">H", b[i:i+2])[0]; i += 2
    for _ in range(na):
        ni = struct.unpack(">H", b[i:i+2])[0]
        ln = struct.unpack(">I", b[i+2:i+6])[0]
        i += 6 + ln
    return i
nf = struct.unpack(">H", b[i:i+2])[0]; i += 2
for _ in range(nf):
    i += 6; i = skip_attrs(i)
nm = struct.unpack(">H", b[i:i+2])[0]; i += 2
for _ in range(nm):
    ma, mn, md = struct.unpack(">HHH", b[i:i+6])
    i += 6
    na = struct.unpack(">H", b[i:i+2])[0]; i += 2
    for _ in range(na):
        an = struct.unpack(">H", b[i:i+2])[0]
        ln = struct.unpack(">I", b[i+2:i+6])[0]
        body = b[i+6:i+6+ln]
        if utf(an) == "Code" and (target == "*" or target in utf(mn)):
            # Code attr body: max_stack(u2) max_locals(u2) code_length(u4) code
            cl = struct.unpack(">I", body[4:8])[0]
            code = body[8:8+cl]
            print(f"=== {utf(mn)} {utf(md)}  ({cl} bytes)")
            # compact opcode walk (only the ops this compiler emits)
            OPS = {
                0x00:"nop",0x01:"aconst_null",0x02:"iconst_m1",0x03:"iconst_0",0x04:"iconst_1",
                0x05:"iconst_2",0x06:"iconst_3",0x07:"iconst_4",0x08:"iconst_5",0x09:"lconst_0",
                0x0a:"lconst_1",0x10:"bipush",0x11:"sipush",0x12:"ldc",0x13:"ldc_w",0x14:"ldc2_w",
                0x15:"iload",0x17:"lload",0x19:"aload",0x1a:"iload_0",0x1b:"iload_1",0x1c:"iload_2",
                0x1d:"iload_3",0x1e:"lload_0",0x1e:"lload_0",0x1f:"lload_1",0x20:"lload_2",0x21:"lload_3",
                0x2a:"aload_0",0x2b:"aload_1",0x2c:"aload_2",0x2d:"aload_3",0x2e:"iaload",
                0x32:"aaload",0x35:"baload",0x36:"istore",0x37:"lstore",0x3a:"astore",
                0x3b:"istore_0",0x3c:"istore_1",0x3d:"istore_2",0x3e:"istore_3",0x3f:"lstore_0",
                0x40:"lstore_1",0x41:"lstore_2",0x42:"lstore_3",0x4b:"astore_0",0x4c:"astore_1",
                0x4d:"astore_2",0x4e:"astore_3",0x4f:"iastore",0x53:"aastore",0x57:"pop",0x58:"pop2",
                0x59:"dup",0x5a:"dup_x1",0x5b:"dup_x2",0x5c:"dup2",0x5f:"swap",
                0x60:"iadd",0x64:"isub",0x68:"imul",0x6c:"idiv",0x70:"irem",0x74:"lneg",
                0x78:"ishl",0x7a:"ishr",0x7c:"iushr",0x80:"ior",0x82:"ixor",
                0x83:"i2l",0x85:"i2f",0x88:"i2d",0x8b:"f2i",0x8e:"d2i",
                0x91:"i2b",0x92:"i2c",0x93:"i2s",0x94:"lcmp",0x95:"fcmpl",0x96:"fcmpg",
                0x97:"dcmpl",0x98:"dcmpg",0x99:"ifeq",0x9a:"ifne",0x9b:"iflt",0x9c:"ifge",
                0x9d:"ifgt",0x9e:"ifle",0x9f:"if_icmpeq",0xa0:"if_icmpne",0xa1:"if_icmplt",
                0xa2:"if_icmpge",0xa3:"if_icmpgt",0xa4:"if_icmple",0xa5:"if_acmpeq",0xa6:"if_acmpne",
                0xa7:"goto",0xac:"ireturn",0xad:"lreturn",0xae:"freturn",0xb0:"areturn",
                0xb1:"return",0xb2:"getstatic",0xb4:"getfield",0xb5:"putfield",
                0xb6:"invokevirtual",0xb7:"invokespecial",0xb8:"invokestatic",
                0xbb:"new",0xbc:"newarray",0xbd:"anewarray",0xbe:"arraylength",
                0xbf:"athrow",0xc0:"checkcast",0xc1:"instanceof",0xc6:"ifnull",0xc7:"ifnonnull",
            }
            wide_sizes = {0x15:2,0x17:2,0x19:2,0x36:2,0x37:2,0x3a:2,0xa9:2,0xc4:0}
            pc = 0
            try:
              while pc < len(code):
                op = code[pc]
                name = OPS.get(op, f"0x{op:02x}")
                sz = 1
                arg = ""
                if op == 0x12: sz = 2; arg = str(ci(code[pc+1]))
                elif op in (0x13, 0x14): sz = 3; arg = str(ci(struct.unpack(">H", code[pc+1:pc+3])[0]))
                elif op in (0xb2, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xbb, 0xbd, 0xc0, 0xc1):
                    sz = 3; arg = str(ci(struct.unpack(">H", code[pc+1:pc+3])[0]))
                elif op in (0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xa0, 0xa1, 0xa2, 0xa3,
                            0xa4, 0xa5, 0xa6, 0xa7, 0xc6, 0xc7):
                    sz = 3; off = struct.unpack(">h", code[pc+1:pc+3])[0]; arg = f"-> {pc+off}"
                elif op in (0x10,): sz = 2; arg = str(code[pc+1])
                elif op in (0x11,): sz = 3; arg = str(struct.unpack(">h", code[pc+1:pc+3])[0])
                elif op in wide_sizes and op != 0xc4: sz = wide_sizes[op]
                elif op == 0xc4:  # wide
                    mop = code[pc+1]; sz = 4
                    arg = f"wide {OPS.get(mop, hex(mop))} idx={struct.unpack('>H', code[pc+2:pc+4])[0]}"
                print(f"  {pc:4d} {name:20s} {arg}")
                pc += sz
            except Exception as e:
                print(f"  DECODE-STOP at pc={pc}: {e}")
                print(f"  RAW-TAIL: {code[pc:pc+16].hex(' ')}")
        i += 6 + ln
