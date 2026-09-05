#!/usr/bin/env python3
"""GOLDEN-02 oracle: dump listener-registration + callback bytecode from the
frozen EXT-01 APK. Independent of the runtime parser (JADX-style check).

Proves from APK bytes alone:
  DEX -> invoke-* -> View.setOnLongClickListener
      -> listener class implements View$OnLongClickListener
      -> callback onLongClick(View)Z
      -> state mutation calls (ClipboardManager.setPrimaryClip / Toast.show)

Usage: dump_apk_interaction.py <apk> [class-substring]
Exit code 0 = all chain links found; 1 = any link missing.
"""
import struct, zipfile, sys

APK = sys.argv[1]
CLS_FILTER = sys.argv[2] if len(sys.argv) > 2 else 'MainActivity'
data = zipfile.ZipFile(APK).read('classes.dex')

def u32(o): return struct.unpack_from('<I', data, o)[0]
def u16(o): return struct.unpack_from('<H', data, o)[0]
def uleb(arr, o):
    r = s = 0
    while True:
        b = arr[o]; o += 1
        r |= (b & 0x7f) << s; s += 7
        if b < 0x80: return r, o

hdr = {
    'string_ids_size': u32(0x38), 'string_ids_off': u32(0x3c),
    'type_ids_size': u32(0x40), 'type_ids_off': u32(0x44),
    'proto_ids_size': u32(0x4c), 'proto_ids_off': u32(0x4c) if False else u32(0x4c),
    'field_ids_size': u32(0x50), 'field_ids_off': u32(0x54),
    'method_ids_size': u32(0x58), 'method_ids_off': u32(0x5c),
    'class_defs_size': u32(0x60), 'class_defs_off': u32(0x64),
}

def get_str(idx):
    off = u32(hdr['string_ids_off'] + 4 * idx)
    _, o = uleb(data, off)
    end = data.index(b'\x00', o)
    return data[o:end].decode('utf-8', 'replace')

def get_type(idx):
    return get_str(u32(hdr['type_ids_off'] + 4 * idx))

def get_mname(mid):
    off = hdr['method_ids_off'] + 8 * mid
    cls = get_type(u16(off)); proto = u16(off + 2); name = get_str(u32(off + 4))
    return cls, name

def get_fname(fid):
    off = hdr['field_ids_off'] + 8 * fid
    cls = get_type(u16(off)); name = get_str(u32(off + 4))
    return cls, name

def method_name(mid):
    return get_mname(mid)[1]

# instruction lengths (16-bit code units) for opcodes present in this DEX
ILEN = {0x00:1,0x01:1,0x04:1,0x07:1,0x08:1,0x09:1,0x0a:1,0x0b:1,0x0c:1,0x0f:1,0x10:1,0x11:1,0x12:1,
        0x14:3,0x1a:2,0x1b:3,0x32:2,0x33:2,0x35:2,0x36:2,0x52:2,0x53:2,0x54:2,0x55:2,0x56:2,0x57:2,
        0x59:2,0x5a:2,0x5b:2,0x5c:2,0x60:2,0x61:2,0x62:2,0x63:2,0x64:2,0x65:2,0x66:2,0x67:2,
        0x6e:3,0x6f:3,0x70:3,0x71:3,0x72:3,0x74:3,0x75:3,0x76:3,0x77:3,0x78:3,0x25:3,
        0x90:2,0x91:2,0x92:2,0x93:2,0x94:2,0x95:2,0x96:2,0x97:2,0x98:2,0x99:2,0x9a:2,0x9b:2,
        0x9c:2,0x9d:2,0x9e:2,0x9f:2,0xa0:2,0xa1:2,0xa2:2,0xa3:2,0xa4:2,0xa5:2,0xa6:2,0xa7:2,
        0xa8:2,0xa9:2,0xaa:2,0xab:2,0xac:2,0xad:2,0xae:2,0xaf:2,
        0xb0:1,0xb1:1,0xb2:1,0xb3:1,0xb4:1,0xb5:1,0xb6:1,0xb7:1,0xb8:1,0xb9:1,0xba:1,
        0xbb:1,0xbc:1,0xbd:1,0xbe:1,0xbf:1,0xc0:1,0xc1:1,
        0xc2:2,0xc3:2,0xc4:2,0xc5:2,0xc6:2,0xc7:2,0xc8:2,0xc9:2,0xca:2,0xcb:2,0xcc:2,0xcd:2,
        0xce:2,0xcf:2,0xd0:2,0xd1:2,0xd2:2,0xd3:2,0xd4:2,0xd5:2,0xd6:2,0xd7:2,
        0xd8:2,0xd9:2,0xda:2,0xdb:2,0xdc:2,0xdd:2,0xde:2,0xdf:2,0xe0:2,0xe1:2,
        0xe2:2,0xe3:2,0xe4:2,0xe5:2,0xe6:2,0xe7:2,0xe8:2,0xe9:2,0xea:2,0xeb:2,0xec:2,0xed:2,0xee:2,0xef:2,
        0xf0:2,0xf1:2,0xf2:2,0xf3:2,0xf4:2,0xf5:2,0xf6:2,0xf7:2,0xf8:2,0xf9:2,0xfa:2,0xfb:2,0xfc:2,0xfd:2,0xfe:2,0xff:2}

# ---- parse class defs, find target class + its class_data ----
target = None
for i in range(hdr['class_defs_size']):
    off = hdr['class_defs_off'] + 32 * i
    cls_idx = u32(off)
    cls = get_type(cls_idx)
    if CLS_FILTER in cls:
        target = {
            'class': cls,
            'access': u32(off + 4),
            'super': get_type(u32(off + 8)) if u32(off + 8) != 0xffffffff else None,
            'interfaces_off': u32(off + 12),
            'class_data_off': u32(off + 24),
        }
if not target:
    print(f'CLASS NOT FOUND: {CLS_FILTER}'); sys.exit(1)

print(f'class: {target["class"]}')
print(f'  super: {target["super"]}')
# interfaces
ioff = target['interfaces_off']
if ioff != 0:
    size = u32(ioff)
    ifaces = []
    for k in range(size):
        ifaces.append(get_type(u16(ioff + 4 + 2 * k)))
    print(f'  interfaces: {ifaces}')
    IFACES = ifaces
else:
    IFACES = []

# ---- parse class_data (direct + virtual methods), then code ----
cd = target['class_data_off']
methods = []
if cd:
    o = cd
    sf, o = uleb(data, o); inf, o = uleb(data, o); dm, o = uleb(data, o); vm, o = uleb(data, o)
    fidx = 0  # consume field entries (own index space)
    for _ in range(sf):
        d, o = uleb(data, o); fidx += d
        _, o = uleb(data, o)
    for _ in range(inf):
        d, o = uleb(data, o); fidx += d
        _, o = uleb(data, o)
    midx = 0
    for _ in range(dm):
        diff, o = uleb(data, o); midx += diff
        acc, o = uleb(data, o); code_off, o = uleb(data, o)
        methods.append(('direct', midx, code_off))
    midx = 0
    for _ in range(vm):
        diff, o = uleb(data, o); midx += diff
        acc, o = uleb(data, o); code_off, o = uleb(data, o)
        methods.append(('virtual', midx, code_off))

# opcode table (subset needed): name + format-instruction fetch
def decode(code, code_off):
    """Decode a code item, print invoked methods/fields and const strings."""
    insns_size = u32(code_off + 12)
    insns_off = code_off + 16
    i = 0
    found = []
    while i < insns_size:
        w = u16(insns_off + 2 * i)
        op = w & 0xff
        # invoke-kind: 0x6e-0x72 (virtual/super/direct/static), 0x74-0x78/range
        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78):
            mid = u16(insns_off + 2 * (i + 1))
            cls, name = get_mname(mid)
            found.append(('invoke', op, cls, name))
            i += 3
        elif 0x52 <= op <= 0x5f:  # iget*/iput* family (22c)
            fid = u16(insns_off + 2 * (i + 1))
            cls, name = get_fname(fid)
            found.append(('ifield', op, cls, name))
            i += 2
        elif 0x60 <= op <= 0x6d:  # sget*/sput* family (21c)
            fid = u16(insns_off + 2 * (i + 1))
            cls, name = get_fname(fid)
            found.append(('sfield', op, cls, name))
            i += 2
        elif op in (0x1a, 0x1b):  # const-string
            sidx = u16(insns_off + 2 * (i + 1)) if op == 0x1a else u32(insns_off + 2 * (i + 1))
            found.append(('const-string', op, None, get_str(sidx)))
            i += 2 if op == 0x1a else 3
        elif op == 0x0e:  # return-void
            found.append(('return-void', op, None, None)); i += 1
        elif op in (0x0f, 0x10, 0x11):  # return / return-wide / return-object
            found.append(('return', op, None, (w >> 8) >> 4)); i += 1
        else:
            i += ILEN.get(op, 1)
    return found

print('  methods:')
CHAIN = {'registration': False, 'iface_impl': False, 'callback': False,
         'toast_maketext': False, 'toast_show': False, 'clipboard': False,
         'return_true': False}
for kind, midx, code_off in methods:
    name = method_name(midx)
    if code_off == 0:
        print(f'    {kind} {name} (abstract/native)')
        continue
    print(f'    {kind} {name} @0x{code_off:x}:')
    for tag, op, cls, nm in decode(code_off, code_off):
        if tag == 'invoke':
            print(f'      invoke op=0x{op:02x} -> {cls}.{nm}')
            if nm == 'setOnLongClickListener': CHAIN['registration'] = True
            if cls == 'Landroid/widget/Toast;' and nm == 'makeText': CHAIN['toast_maketext'] = True
            if cls == 'Landroid/widget/Toast;' and nm == 'show': CHAIN['toast_show'] = True
            if 'Clipboard' in (cls or '') or nm == 'setPrimaryClip' or nm == 'copyText': CHAIN['clipboard'] = True
        elif tag == 'const-string':
            print(f'      const-string "{nm[:60]}"')
        elif tag in ('ifield', 'sfield'):
            print(f'      {tag} op=0x{op:02x} -> {cls}.{nm}')

# onLongClick: proper linear decode with const-tracking of the RETURN register
for kind, midx, code_off in methods:
    if method_name(midx) == 'onLongClick' and code_off:
        CHAIN['callback'] = True
        if 'Landroid/view/View$OnLongClickListener;' in IFACES: CHAIN['iface_impl'] = True
        insns_size = u32(code_off + 12); insns_off = code_off + 16
        const_reg = {}          # reg -> value from const/4
        i = 0
        while i < insns_size:
            w = u16(insns_off + 2 * i)
            op = w & 0xff
            n = ILEN.get(op)
            if n is None:
                print(f'      decode stop: unknown op 0x{op:02x} @[{i}]'); break
            if op == 0x12:  # const/4 vA, #+B (11n)
                A = (w >> 8) >> 4; B = (w >> 8) & 0xf
                val = B - 16 if B > 7 else B
                const_reg[A] = val
            elif op in (0x0f, 0x10, 0x11):  # return vAA
                A = (w >> 8)
                if A in const_reg and const_reg[A] == 1:
                    CHAIN['return_true'] = True
                    print(f'  onLongClick returns TRUE (const/4 v{A}, 0x1 @[{i}]; return v{A}) proven')
            i += n

print()
print('=== CHAIN LINKS (APK-bytes oracle) ===')
ok = True
for k, v in CHAIN.items():
    print(f'  {"PASS" if v else "MISS"}  {k}')
    ok = ok and v
sys.exit(0 if ok else 1)
