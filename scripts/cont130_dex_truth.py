#!/usr/bin/env python3
"""CONT-130 v2: correct 8-byte method_id_item stride — AndroidApplication byte truth."""
import struct, zipfile

APK = "/home/z/my-project/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk"
TARGET = "Lcom/badlogic/gdx/backends/android/AndroidApplication;"
z = zipfile.ZipFile(APK); dex = z.read("classes.dex")

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

str_size, str_off = struct.unpack_from("<2I", dex, 0x38)
type_size, type_off = struct.unpack_from("<2I", dex, 0x40)
m_size, m_off = struct.unpack_from("<2I", dex, 0x58)
c_size, c_off = struct.unpack_from("<2I", dex, 0x60)
str_off_arr = struct.unpack_from(f"<{str_size}I", dex, str_off)

def str_at(si):
    off = str_off_arr[si]
    _, o = uleb(dex, off)
    return dex[o:dex.index(b"\x00", o)].decode("utf-8", "replace")

tds = [str_at(struct.unpack_from("<I", dex, type_off + t * 4)[0]) for t in range(type_size)]

def mid(idx):  # method_id_item = u16 class_idx, u16 proto_idx, u32 name_idx = 8 bytes
    ci, pi, ni = struct.unpack_from("<HHI", dex, m_off + idx * 8)
    return tds[ci], str_at(ni)

for probe in (0, 1, 1135, 1184):
    print(f"method_ids[{probe}] = {mid(probe)}")

for c in range(c_size):
    cd = struct.unpack_from("<8I", dex, c_off + c * 32)
    if tds[cd[0]] != TARGET:
        continue
    o = cd[6]
    sfs, o = uleb(dex, o); ifs, o = uleb(dex, o); dms, o = uleb(dex, o); vms, o = uleb(dex, o)
    print(f"class_data_off=0x{cd[6]:x} hdr {sfs}/{ifs}/{dms}/{vms}")
    for _ in range(sfs + ifs):
        _, o = uleb(dex, o); _, o = uleb(dex, o)
    midx = 0
    print("DIRECT:")
    dm_idx = []
    for i in range(dms):
        diff, o = uleb(dex, o); acc, o = uleb(dex, o); code, o = uleb(dex, o)
        midx += diff
        dm_idx.append(midx)
        print(f"  DM[{i}] m_idx={midx} acc={acc:#x} code_off={code:#x} -> {mid(midx)[0]}.{mid(midx)[1]}")
    print("VIRTUAL (first 6):")
    for i in range(min(6, vms)):
        diff, o = uleb(dex, o); acc, o = uleb(dex, o); code, o = uleb(dex, o)
        midx += diff
        print(f"  VM[{i}] m_idx={midx} acc={acc:#x} code_off={code:#x} -> {mid(midx)[0]}.{mid(midx)[1]}")
    print(f"  ... total VM={vms}; last m_idx={midx}")
    oc = [i for i in range(m_size) if mid(i)[0] == TARGET and mid(i)[1] == "onCreate"]
    print(f"method_ids with {TARGET}.onCreate: {oc} (engine recorded method_id=1184)")
    if 1184 < m_size:
        print(f"method_ids[1184] = {mid(1184)[0]}.{mid(1184)[1]}")
    # what is 1135 (first direct per bytes)?
    break
