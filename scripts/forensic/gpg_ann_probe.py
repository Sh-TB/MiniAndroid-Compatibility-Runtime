#!/usr/bin/env python3
"""GPG-087 ground truth: parse class_def annotations_off for given classes.

DEX law (AOSP libdexfile): class_def_item.annotations_off ->
  annotation_set_item { size u32; annotation_off_item[size] u32 }
  each -> annotation_item { visibility u8 (0x01=RUNTIME, 0x00=BUILD, 0x02=SYSTEM),
    encoded_annotation { type_idx ULEB; size ULEB; (name_idx ULEB, encoded_value)* } }

Answers: does Landroidx/navigation/compose/e; carry a RUNTIME annotation
of type Landroidx/navigation/l$b; (= Navigator.Name post-R8)? With which
element values?
"""
import struct, sys, zipfile

apk = sys.argv[1]
want_only = sys.argv[2:] or ["Landroidx/navigation/compose/e;",
                          "Landroidx/navigation/l$b;",
                          "Landroidx/navigation/h;"]
z = zipfile.ZipFile(apk)
d = z.read('classes.dex')

u4 = lambda o: struct.unpack_from('<I', d, o)[0]
u2 = lambda o: struct.unpack_from('<H', d, o)[0]
u1 = lambda o: d[o]

def uleb(p):
    r = 0; s = 0
    while True:
        b = u1(p+s); r |= (b & 0x7f) << (7*s); s += 1
        if not (b & 0x80): return r, p+s

def sleb(p):
    r = 0; s = 0
    while True:
        b = u1(p+s); r |= (b & 0x7f) << (7*s); s += 1
        if not (b & 0x80):
            if b & 0x40 and s < 8: r |= -(1 << (7*s))
            return r, p+s

s_sz, s_off = u4(0x38), u4(0x3c)
t_sz, t_off = u4(0x40), u4(0x44)
p_sz, p_off = u4(0x48), u4(0x4c)
f_sz, f_off = u4(0x50), u4(0x54)
m_sz, m_off = u4(0x58), u4(0x5c)
c_sz, c_off = u4(0x60), u4(0x64)

strs = []
for i in range(s_sz):
    off = u4(s_off + 4*i)
    n, p2 = uleb(off)
    strs.append(d[p2:p2+n].decode('utf-8', 'replace'))
def tdesc(i): return strs[u4(t_off + 4*i)]
def pname(i): return strs[i]  # encoded_annotation name_idx indexes string_ids directly

def read_enc_value(p):
    """Return (python_value, next_offset) for an encoded_value at p."""
    arg_and_vt = u1(p); vt = arg_and_vt & 0x1f; arg = arg_and_vt >> 5
    q = p + 1
    if vt == 0x00:   # BYTE
        v = u1(q) & 0xff if arg == 0 else 0
        return v, q + arg + 1
    if vt == 0x02:   # SHORT
        v, q2 = sleb(q); return v, q2
    if vt == 0x03:   # CHAR
        raw = int.from_bytes(d[q:q+arg+1], 'little'); return chr(raw), q+arg+1
    if vt == 0x04:   # INT
        v, q2 = sleb(q); return v, q2
    if vt == 0x06:   # LONG
        v, q2 = sleb(q); return v, q2
    if vt == 0x10:   # FLOAT
        raw = int.from_bytes(d[q:q+arg+1], 'little') << (8*(3-arg))
        return struct.unpack('<f', struct.pack('<I', raw))[0], q+arg+1
    if vt == 0x11:   # DOUBLE
        raw = int.from_bytes(d[q:q+arg+1], 'little') << (8*(7-arg))
        return struct.unpack('<d', struct.pack('<Q', raw))[0], q+arg+1
    if vt == 0x15:   # METHOD_TYPE
        idx, q2 = uleb(q); return ("methodtype", strs[idx] if idx < s_sz else idx), q2
    if vt == 0x16:   # METHOD_HANDLE
        idx, q2 = uleb(q); return ("mh", idx), q2
    if vt == 0x17:   # STRING
        idx, q2 = uleb(q); return strs[idx] if idx < s_sz else f"<str:{idx}>", q2
    if vt == 0x18:   # TYPE
        idx, q2 = uleb(q); return tdesc(idx) if idx < t_sz else f"<type:{idx}>", q2
    if vt == 0x19:   # FIELD
        idx, q2 = uleb(q); return ("field", idx), q2
    if vt == 0x1a:   # METHOD
        idx, q2 = uleb(q); return ("method", idx), q2
    if vt == 0x1b:   # ENUM
        idx, q2 = uleb(q); return ("enum", idx), q2
    if vt == 0x1c:   # ARRAY
        n, q2 = uleb(q)
        out = []
        for _ in range(n):
            v, q2 = read_enc_value(q2); out.append(v)
        return out, q2
    if vt == 0x1d:   # ANNOTATION
        tidx, q2 = uleb(q)
        n, q2 = uleb(q2)
        els = {}
        for _ in range(n):
            nidx, q2 = uleb(q2)
            v, q2 = read_enc_value(q2)
            els[pname(nidx)] = v
        return ("annotation", tdesc(tidx), els), q2
    if vt == 0x1e:   # NULL
        return None, q
    if vt == 0x1f:   # BOOLEAN
        return bool(arg), q
    return f"<vt:{vt:#x}>", q + arg + 1

def parse_annotation_item(off):
    vis = u1(off)
    q = off + 1
    tidx, q = uleb(q)
    n, q = uleb(q)
    els = {}
    for _ in range(n):
        nidx, q = uleb(q)
        v, q = read_enc_value(q)
        els[pname(nidx)] = v
    visname = {0: 'BUILD', 1: 'RUNTIME', 2: 'SYSTEM'}.get(vis, f'?{vis}')
    return visname, tdesc(tidx), els

def parse_set(off, label):
    if off == 0 or off + 4 > len(d):
        return
    asz = u4(off)
    if asz > 0x10000:
        print(f"  {label}: bogus set size {asz} @ {off:#x}")
        return
    print(f"  {label} @ {off:#x}: {asz} entries")
    for k in range(asz):
        aoff = u4(off + 4 + 4*k)
        print(f"    item{k} @ {aoff:#x} vis_byte={d[aoff]:#x}", end='')
        try:
            vis, tname, els = parse_annotation_item(aoff)
            print(f" vis={vis} type={tname} elements={els}")
        except Exception as e:
            print(f" PARSE-ERR {e}")

for ci in range(c_sz):
    co = c_off + 32*ci
    cls_idx = u4(co)
    ann_off = u4(co + 20)   # annotations_off
    cls = tdesc(cls_idx)
    if want_only and cls not in want_only:
        continue
    print(f"CLASS {cls}")
    if ann_off == 0:
        print("  (no annotations directory)")
        continue
    # DEX law: annotations_off points at annotation_set_item OR
    # annotation_directory_item (when field/method/param annotations exist).
    # Directory: { class_annotations_off u32; fields_size u32; methods_size u32;
    #              params_size u32; ... }. Detect: u32[0] is a sane file offset
    # pointing at a set whose size is sane.
    cand0 = u4(ann_off)
    is_dir = (cand0 < len(d) and cand0 != 0 and (cand0 & 3) == 0 and
              u4(ann_off + 4) < 0x10000 and u4(ann_off + 8) < 0x10000 and
              u4(ann_off + 12) < 0x10000 and
              cand0 + 4 <= len(d) and u4(cand0) <= 0x1000)
    if is_dir:
        cls_ann = u4(ann_off)
        fsz = u4(ann_off + 4); msz = u4(ann_off + 8); psz = u4(ann_off + 12)
        print(f"  annotation_directory_item @ {ann_off:#x}: class_ann={cls_ann:#x} fields={fsz} methods={msz} params={psz}")
        parse_set(cls_ann, "class annotations")
        q = ann_off + 16
        for _ in range(fsz):
            fidx = u4(q); so = u4(q+4); q += 8
            print(f"  field idx {fidx}:"); parse_set(so, "  field ann set")
        for _ in range(msz):
            midx = u4(q); so = u4(q+4); q += 8
            print(f"  method idx {midx}:"); parse_set(so, "  method ann set")
        for _ in range(psz):
            midx = u4(q); so = u4(q+4); q += 8
            print(f"  param anns for method idx {midx}:"); parse_set(so, "  param ann set")
    else:
        parse_set(ann_off, "annotations")
