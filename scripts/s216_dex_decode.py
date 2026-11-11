#!/usr/bin/env python3
"""S216 CONT-131 decode v2 — raw-struct DEX truth for the dooz pointer-resume
chain. Uses the proven cont130 parser shape (uleb-driven class_data walk).
Dumps the method table of Liw0; Lbo; Lsj; Lbt1; Lss1; La00; + disassembles the
invoke sites of the resume-critical methods."""
import struct, zipfile

APK = "/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
TARGETS = {"Liw0;", "Lbo;", "Lsj;", "Lbt1;", "Lss1;", "La00;"}

z = zipfile.ZipFile(APK)


def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80):
            break
        s += 7
    return r, o


for dn in [n for n in z.namelist() if n.endswith('.dex')]:
    dex = z.read(dn)
    str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
    type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
    m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
    c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
    str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)

    def str_at(si):
        off = str_off_arr[si]
        _, o = uleb(dex, off)
        return dex[o:dex.index(b"\x00", o)].decode("utf-8", "replace")

    tds = [str_at(struct.unpack_from("<I", dex, type_off + t * 4)[0])
           for t in range(type_size)]

    def mid(idx):
        ci, pi, ni = struct.unpack_from("<HHI", dex, m_off + idx * 8)
        return tds[ci], str_at(ni)

    hits = []
    for c in range(c_size):
        cd = struct.unpack_from("<8I", dex, c_off + c * 32)
        if tds[cd[0]] not in TARGETS:
            continue
        hits.append(cd)
    if not hits:
        continue
    for cd in hits:
        cls = tds[cd[0]]
        sup = tds[cd[2]] if cd[2] != 0xFFFFFFFF else "?"
        o = cd[6]
        sfs, o = uleb(dex, o); ifs, o = uleb(dex, o)
        dms, o = uleb(dex, o); vms, o = uleb(dex, o)
        print(f"=== {cls} super={sup} ({dn}) d/v={dms}/{vms}")
        for _ in range(sfs + ifs):
            _, o = uleb(dex, o); _, o = uleb(dex, o)
        midx = 0
        for i in range(dms + vms):
            diff, o = uleb(dex, o); acc, o = uleb(dex, o); code, o = uleb(dex, o)
            midx += diff
            cc, nm = mid(midx)
            # descriptor: need proto; approximate with name only here
            print(f"  [{i}] {nm} class={cc} acc=0x{acc:x} code=0x{code:x}")
