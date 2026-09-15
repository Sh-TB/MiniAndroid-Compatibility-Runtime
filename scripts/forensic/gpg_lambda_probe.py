#!/usr/bin/env python3
"""GAME PLAYABILITY GATE — rememberSaveable init-lambda blocker, DEX ground truth v2.

User question set:
  Q1. What should invoke the init lambda?      (remember{} -> Composer.cache / holder)
  Q2. Via which interface/class is it dispatched? (Function0.invoke sites)
  Q3. What is the real receiver at that site?  (lambda instance class)
  Q4. What is the exact method descriptor?
  Q5. Why doesn't the engine bridge invoke it?

Probe:
  [1] Find every method that calls Landroidx/navigation/m;.a  (addNavigator)
      -> the createNavController implementation (3 adds expected).
  [2] Dump Landroidx/navigation/m;.b (getNavigator ISE site).
  [3] For the createNavController class: find who instantiates it / passes it
      as a lambda (new-instance + <init> sites, references).
  [4] Find Composer.cache machinery: methods named 'cache', Function0.invoke,
      and every invoke-interface on Lkotlin/jvm/functions/Function0;.invoke
      inside the classes on the navigation chain.
  [5] Locate rememberSaveable implementation class (string refs SaveableHolder).

Usage: python3 scripts/forensic/gpg_lambda_probe.py <apk>
"""
import struct, sys, zipfile

apk = sys.argv[1]
z = zipfile.ZipFile(apk)
names = [n for n in z.namelist() if n.endswith('.dex')]

# Dalvik instruction sizes in 16-bit code units (opcode -> size)
SZ = {}
for op in range(0x100): SZ[op] = 1  # default 1, correct for most
for op in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f, 0x20,
           0x22, 0x23, 0x28, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38,
           0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
           0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x4f, 0x50, 0x51):
    SZ[op] = 2
for op in range(0x52, 0x6e): SZ[op] = 2          # iget..sput family
for op in (0x14, 0x17, 0x24, 0x25, 0x26, 0x2a, 0x2b, 0x29, 0x6e, 0x6f, 0x70, 0x71,
           0x72, 0x74, 0x75, 0x76, 0x77, 0x78, 0xfc, 0xfd, 0xfe, 0xff):
    SZ[op] = 3
for op in range(0x2c, 0x32): SZ[op] = 2      # cmp ops 23x
for op in range(0x90, 0xb0): SZ[op] = 2      # binop 23x
for op in range(0xd0, 0xd8): SZ[op] = 2      # binop/lit16
for op in range(0xd8, 0xe3): SZ[op] = 2      # binop/lit8
for op in (0x18,): SZ[op] = 5
for op in (0xfa, 0xfb): SZ[op] = 4

for dexname in names:
    d = z.read(dexname)
    def u4(o): return struct.unpack_from('<I', d, o)[0]
    def u2(o): return struct.unpack_from('<H', d, o)[0]
    def u1(o): return d[o]
    def uleb(p):
        r = 0; s = 0
        while True:
            b = d[p + s]; r |= (b & 0x7f) << (7 * s); s += 1
            if not (b & 0x80): return r, p + s
    s_sz, s_off = u4(0x38), u4(0x3c)
    t_sz, t_off = u4(0x40), u4(0x44)
    p_sz, p_off = u4(0x48), u4(0x4c)
    f_sz, f_off = u4(0x50), u4(0x54)
    m_sz, m_off = u4(0x58), u4(0x5c)
    c_sz, c_off = u4(0x60), u4(0x64)
    strs = []
    for i in range(s_sz):
        off = u4(s_off + 4 * i)
        n, p2 = uleb(off)
        strs.append(d[p2:p2 + n].decode('utf-8', 'replace'))
    def type_desc(i): return strs[u4(t_off + 4 * i)]
    def proto(i):
        base = p_off + 12 * i
        shorty = strs[u4(base)]
        ret = type_desc(u4(base + 4))
        poff = u4(base + 8)
        params = []
        if poff:
            n = u4(poff)
            for k in range(n):
                params.append(type_desc(u2(poff + 4 + 2 * k)))
        return shorty, ret, params
    def method_ref(i):
        if i >= m_sz:
            raise IndexError(f"method idx {i} >= {m_sz}")
        base = m_off + 8 * i
        cls = type_desc(u2(base))
        name = strs[u4(base + 4)]
        return cls, name, proto(u2(base + 2))
    class_defs = []
    for i in range(c_sz):
        base = c_off + 32 * i
        class_defs.append({
            'class': type_desc(u4(base)),
            'access': u4(base + 4),
            'super': type_desc(u4(base + 8)) if u4(base + 8) != 0xffffffff else '<none>',
            'interfaces_off': u4(base + 12),
            'class_data_off': u4(base + 24),
        })
    by_name = {cd['class']: cd for cd in class_defs}

    def methods_of(cd):
        off = cd.get('class_data_off')
        if not off: return [], []
        p = off
        sf, p = uleb(p); inf, p = uleb(p)
        sm, p = uleb(p); vm, p = uleb(p)
        idx = 0
        for k in range(sf):
            d1, p = uleb(p); d2, p = uleb(p); idx += d1
        idx = 0
        for k in range(inf):
            d1, p = uleb(p); d2, p = uleb(p); idx += d1
        directs = []; idx = 0
        for k in range(sm):
            d1, p = uleb(p); acc, p = uleb(p); co, p = uleb(p); idx += d1
            directs.append((idx, co, acc))
        virts = []; idx = 0
        for k in range(vm):
            d1, p = uleb(p); acc, p = uleb(p); co, p = uleb(p); idx += d1
            virts.append((idx, co, acc))
        return directs, virts

    def code_of(code_off):
        if not code_off: return None, 0
        insns_size = u4(code_off + 12)
        return code_off + 16, insns_size

    def invoke_sites(insns_off, insns_size):
        """Safe linear scan: [(pc, opname, cls.name, params, ret)]."""
        out = []
        i = 0
        end = min(insns_size, (len(d) - insns_off) // 2)
        while i < end:
            w = u2(insns_off + 2 * i)
            op = w & 0xff
            try:
                if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                    cls, name, (shorty, ret, params) = method_ref(u2(insns_off + 2 * (i + 1)))
                    kind = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
                            0x71: 'invoke-static', 0x72: 'invoke-interface'}[op]
                    out.append((i * 2, kind, f"{cls}.{name}", params, ret))
                elif op in (0x74, 0x75, 0x76, 0x77, 0x78):
                    # 3rc format: word1=op|size, word2=method_idx@u2, word3=first reg
                    cls, name, (shorty, ret, params) = method_ref(u2(insns_off + 2 * (i + 1)))
                    kind = {0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
                            0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
                            0x78: 'invoke-interface/range'}[op]
                    out.append((i * 2, kind, f"{cls}.{name}", params, ret))
            except (IndexError, struct.error):
                pass
            step = SZ.get(op, 1)
            i += step
        return out

    def type_sites(insns_off, insns_size, want):
        out = []
        i = 0
        end = min(insns_size, (len(d) - insns_off) // 2)
        while i < end:
            w = u2(insns_off + 2 * i)
            op = w & 0xff
            if op == 0x22 and type_desc(u2(insns_off + 2 * (i + 1))) == want:
                out.append((i * 2, 'new-instance'))
            elif op == 0x1c and type_desc(u2(insns_off + 2 * (i + 1))) == want:
                out.append((i * 2, 'const-class'))
            elif op == 0x1f and type_desc(u2(insns_off + 2 * (i + 1))) == want:
                out.append((i * 2, 'check-cast'))
            i += SZ.get(op, 1)
        return out

    def dump_disasm(insns_off, insns_size, max_pc=None):
        i = 0
        while i < insns_size:
            pc = i * 2
            if max_pc and pc > max_pc: break
            w = u2(insns_off + 2 * i)
            op = w & 0xff
            note = ''
            if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                cls, name, (shorty, ret, params) = method_ref(u2(insns_off + 2 * (i + 1)))
                kind = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
                        0x71: 'invoke-static', 0x72: 'invoke-interface'}[op]
                note = f"{kind} {cls}.{name} {params} -> {ret}"
            elif op in (0x74, 0x75, 0x76, 0x77, 0x78):
                cls, name, (shorty, ret, params) = method_ref(u2(insns_off + 2 * (i + 1)))
                kind = {0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
                        0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
                        0x78: 'invoke-interface/range'}[op]
                note = f"{kind} {cls}.{name} {params} -> {ret}"
            elif op == 0x22:
                note = f"new-instance {type_desc(u2(insns_off + 2 * (i + 1)))}"
            elif op == 0x1a:
                note = f"const-string \"{strs[u2(insns_off + 2 * (i + 1))][:70]}\""
            elif op == 0x1b:
                note = f"const-string/jumbo \"{strs[u4(insns_off + 2 * (i + 1))][:70]}\""
            elif op in range(0x52, 0x6e):
                fbase = f_off + 8 * u2(insns_off + 2 * (i + 1))
                cls = type_desc(u2(fbase)); typ = type_desc(u2(fbase + 2))
                name = strs[u4(fbase + 4)]
                nm = {0x52:'iget',0x53:'iget-wide',0x54:'iget-object',0x55:'iget-boolean',
                      0x56:'iget-byte',0x57:'iget-char',0x58:'iget-short',0x59:'iput',
                      0x5a:'iput-wide',0x5b:'iput-object',0x5c:'iput-boolean',0x5d:'iput-byte',
                      0x5e:'iput-char',0x5f:'iput-short',0x60:'sget',0x61:'sget-wide',
                      0x62:'sget-object',0x63:'sget-boolean',0x64:'sget-byte',
                      0x65:'sget-char',0x66:'sget-short',0x67:'sput',0x68:'sput-wide',
                      0x69:'sput-object',0x6a:'sput-boolean',0x6b:'sput-byte',
                      0x6c:'sput-char',0x6d:'sput-short'}[op]
                note = f"{nm} {cls}.{name}:{typ}"
            elif op in (0x37,0x38,0x39,0x3a,0x3b,0x3c):
                off = struct.unpack_from('<h', d, insns_off + 2 * (i + 1))[0]
                note = f"if-z v{w >> 8 & 0xf}, +{off}"
            print(f"    @{pc:04x} {note}" if note else f"    @{pc:04x} op={hex(op)}")
            i += SZ.get(op, 1)

    print(f"===== {dexname}: {len(class_defs)} classes =====")

    # ---- [1] callers of addNavigator ----
    ADDNAV = ('Landroidx/navigation/m;', 'a')
    print(f"\n[1] METHODS CALLING {ADDNAV[0]}.{ADDNAV[1]} (addNavigator):")
    creators = []
    for cd in class_defs:
        directs, virts = methods_of(cd)
        for midx, co, acc in directs + virts:
            cls, name, (shorty, ret, params) = method_ref(midx)
            io, isz = code_of(co)
            if not io or not isz or isz > 6000: continue
            for pc, kind, m, params2, ret2 in invoke_sites(io, isz):
                if m == f"{ADDNAV[0]}.{ADDNAV[1]}":
                    creators.append((cls, name, params, ret, co))
                    print(f"  {cls}.{name} {params} -> {ret} (code_off={hex(co)})")

    # ---- [2] dump getNavigator ISE site ----
    for cd in class_defs:
        if cd['class'] != 'Landroidx/navigation/m;': continue
        directs, virts = methods_of(cd)
        for midx, co, acc in directs + virts:
            cls, name, (shorty, ret, params) = method_ref(midx)
            if name != 'b': continue
            io, isz = code_of(co)
            print(f"\n[2] Landroidx/navigation/m;.{name} {params} -> {ret} code={hex(co)}")
            dump_disasm(io, isz)

    # ---- [3] dump the creator methods fully ----
    for cls, name, params, ret, co in creators:
        cd = by_name.get(cls)
        if not cd: continue
        io, isz = code_of(co)
        print(f"\n[3] CREATOR {cls}.{name} {params} -> {ret} (code={hex(co)})")
        # interfaces of the class
        ifoff = cd['interfaces_off']
        itypes = []
        if ifoff:
            n = u4(ifoff)
            itypes = [type_desc(u2(ifoff + 4 + 2 * k)) for k in range(n)]
        print(f"    class {cls} super={cd['super']} interfaces={itypes}")
        dump_disasm(io, isz)

    # ---- [4] Function0 machinery on the creator classes ----
    print("\n[4] FUNCTION0 DISPATCH SITES on creator classes + neighbors:")
    fn_invoke = 'Lkotlin/jvm/functions/Function0;.invoke'
    fn_classes = set()
    for cls, name, params, ret, co in creators:
        fn_classes.add(cls)
    for cd in class_defs:
        if cd['class'] not in fn_classes: continue
        directs, virts = methods_of(cd)
        for midx, co, acc in directs + virts:
            mcls, mname, (shorty, ret, params) = method_ref(midx)
            io, isz = code_of(co)
            if not io or not isz: continue
            for pc, kind, m, params2, ret2 in invoke_sites(io, isz):
                if 'Function0' in m and kind.startswith('invoke-interface'):
                    print(f"  {mcls}.{mname}: @{hex(pc)} {kind} {m}")

    # ---- [5] rememberSaveable impl ----
    print("\n[5] rememberSaveable / SaveableHolder strings:")
    hit = [s for s in strs if 'SaveableHolder' in s or s == 'rememberSaveable' or 'RememberSaveable' in s]
    for s in hit[:10]: print(f"  string: {s[:110]}")
    for cd in class_defs:
        directs, virts = methods_of(cd)
        for midx, co, acc in directs + virts:
            cls, name, (shorty, ret, params) = method_ref(midx)
            if name in ('rememberSaveable',) or 'Saveable' in cls:
                if 'compose/runtime' in cls:
                    print(f"  {cls}.{name} {params} -> {ret} code={hex(co)}")

    break
