#!/usr/bin/env python3
"""S204 — enumerate every method of the app's board classes and census the
gdx/GL methods they invoke (dex ground truth for the DrawElements route)."""
import struct, sys, zipfile

sys.path.insert(0, "/home/z/my-project/miniandroid/tools")
import dump_method_bytecode as d  # noqa

APK = '/home/z/my-project/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
CLASSES = ["Lcom/emmanuelmess/tictactoe/DrawableShape;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeRenderer;",
           "Lcom/emmanuelmess/tictactoe/OActor;",
           "Lcom/emmanuelmess/tictactoe/XActor;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeText;",
           "Lcom/emmanuelmess/tictactoe/XOText;"]


def enum_methods(dex, desc):
    """Walk class_def table; return [(name, proto, code_off)] for desc."""
    out = []
    # reuse DexFile internals: class_defs offsets
    d_ = dex.d if hasattr(dex, 'd') else None
    return out


with zipfile.ZipFile(APK) as z:
    data = z.read('classes.dex')

# Minimal class_def walk (independent of dumper internals):
sz, off = struct.unpack_from('<II', data, 0x60)  # class_defs_size/off
str_ids = struct.unpack_from('<II', data, 0x38)
type_ids = struct.unpack_from('<II', data, 0x40)
proto_ids = struct.unpack_from('<II', data, 0x48)
field_ids = struct.unpack_from('<II', data, 0x50)
meth_ids = struct.unpack_from('<II', data, 0x58)

ssoff = str_ids[1]
toff = type_ids[1]
poff = proto_ids[1]
moff = meth_ids[1]
coff = off

_str_cache = {}


def get_s(idx):
    if idx in _str_cache:
        return _str_cache[idx]
    o = struct.unpack_from('<I', data, ssoff + 4 * idx)[0]
    p, shift, ln = o, 0, 0
    while True:
        b = data[p]
        ln |= (b & 0x7f) << shift
        p += 1
        if not (b & 0x80):
            break
        shift += 7
    val = data[p:p + ln].decode('utf-8', 'replace')
    _str_cache[idx] = val
    return val


def get_t(idx):
    return get_s(struct.unpack_from('<I', data, toff + 4 * idx)[0])


def get_m(idx):
    mid = meth_ids[1] + 8 * idx
    a, b, c = struct.unpack_from('<HHI', data, mid)
    return get_t(a), get_s(c)  # class_idx, name_idx


def uleb(p):
    r, s = 0, 0
    while True:
        b = data[p]
        r |= (b & 0x7f) << s
        p += 1
        if not (b & 0x80):
            return r, p
        s += 7


for ci in range(sz):
    cd = coff + 32 * ci
    cidx = struct.unpack_from('<I', data, cd)[0]
    desc = get_t(cidx)
    if desc not in CLASSES:
        continue
    # class_data_off
    cdo = struct.unpack_from('<I', data, cd + 24)[0]
    print(f"\n=== {desc} ===")
    if not cdo:
        continue
    p = cdo
    sf, p = uleb(p)
    inf, p = uleb(p)
    dm, p = uleb(p)
    vm, p = uleb(p)
    # fields: encoded_field = idx_diff:access_flags (uleb pairs)
    fidx = 0
    for _ in range(sf + inf):
        a, p = uleb(p)
        b, p = uleb(p)
        fidx += a
    midx = 0
    for _ in range(dm + vm):
        a, p = uleb(p)
        b, p = uleb(p)
        midx += a
        mdesc, mname = get_m(midx)
        # code_off follows unless abstract/native
        flags = b
        has_code = (flags & 0x500) == 0  # ACC_NATIVE|ACC_ABSTRACT lack code
        code_off = 0
        if has_code:
            code_off, p = uleb(p)
        tag = 'direct' if _ < dm else 'virtual'
        print(f"  {mdesc} {mname} flags=0x{flags:x} code=0x{code_off:x}")
