#!/usr/bin/env python3
"""cont48_f1_drawable_probe.py — F1 step 3: probe ONE drawable resid end-to-end
through the raw ARSC: 0x7f080016 (R$drawable first field). Prints the entry's
Res_value type + string + whether the path exists in the APK zip."""
import struct, zipfile

apk_path = "/home/z/my-project/upload/telegram_official.apk"
z = zipfile.ZipFile(apk_path)
data = z.read("resources.arsc")
def u16(o): return struct.unpack_from("<H", data, o)[0]
def u32(o): return struct.unpack_from("<I", data, o)[0]

# global string pool (for Res_value STRING data indices)
gpool_off = u16(2)
gp_hdr, gp_size = u16(gpool_off+2), u32(gpool_off+4)
def gstring(i):
    o = u32(gpool_off + 28 + i*4)
    p = gpool_off + u32(gpool_off+20) + o
    n = u16(p)
    if n & 0x8000: n = ((n & 0x7fff) << 16) | u16(p+2); p += 4
    else: p += 2
    return data[p:p+n*2].decode("utf-16-le", "replace")

# package
pos = gpool_off + gp_size
while pos + 8 <= len(data):
    ct = u16(pos)
    if ct == 0x0200: break
    pos += u32(pos+4)
po = pos; phdr = u16(pos+2)
ts_off = u32(po+268)
p2 = po + phdr
if ts_off and p2 == po + ts_off: p2 += u32(p2+4)
ks_off = u32(po+276)
if ks_off and p2 == po + ks_off: p2 += u32(p2+4)

TARGET_RESID = 0x7f080016
want_type, want_entry = (TARGET_RESID >> 16) & 0xFF, TARGET_RESID & 0xFFFF

found = 0
while p2 + 8 <= len(data):
    ct, chdr, csz = u16(p2), u16(p2+2), u32(p2+4)
    if csz == 0: break
    if ct == 0x0201:
        tid = data[p2+8]; flags = data[p2+9]
        ec = u32(p2+12); estart = u32(p2+16)
        if tid == want_type and not (flags & 1):   # dense chunk
            if want_entry < ec:
                off = u32(p2 + chdr + want_entry*4)
                if off != 0xFFFFFFFF:
                    ep = p2 + estart + off
                    eflags = u16(ep+2)
                    esize = u16(ep)
                    compact = (eflags & 0x0008) != 0
                    print(f"entry found: chunk hdr={chdr} flags={flags:#x} ec={ec}")
                    print(f"  entry: size={esize} eflags={eflags:#06x} compact={compact}")
                    if compact:
                        dt = eflags >> 8
                        val = u32(ep+4)
                        print(f"  COMPACT value dataType={dt:#04x} data={val:#x}")
                    else:
                        key = u32(ep+4)
                        vsize = u16(ep+8); vres = u16(ep+10)
                        vtype = data[ep+12]
                        vdata = u32(ep+16)
                        print(f"  value: size={vsize} res={vres:#x} type={vtype:#04x} data={vdata:#x}")
                        if vtype == 0x03:
                            s = gstring(vdata)
                            print(f"  STRING -> {s!r}")
                            try:
                                zi = z.getinfo(s)
                                print(f"  ZIP: EXISTS size={zi.file_size}")
                            except KeyError:
                                print("  ZIP: MISSING")
                    found += 1
    p2 += csz
print("probed entries:", found)
