#!/usr/bin/env python3
"""cont12_try_table.py — print the try/catch table of one method.
Usage: cont12_try_table.py <apk> <code_item_file_offset_hex>"""
import struct, zipfile, sys

def uleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80): break
        s += 7
    return r, o

def sleb(b, o):
    r = 0; s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7F) << s
        s += 7
        if not (x & 0x80):
            if x & 0x40 and s < 64:
                r |= -(1 << s)
            break
    return r, o

def main():
    apk, code_hex = sys.argv[1], sys.argv[2]
    code_off = int(code_hex, 16)
    zf = zipfile.ZipFile(apk)
    data = None
    for dn in [n for n in zf.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        d = zf.read(dn)
        type_size, type_off = struct.unpack_from('<2I', d, 0x40)
        str_size, str_off = struct.unpack_from('<2I', d, 0x38)
        soa = struct.unpack_from(f'<{str_size}I', d, str_off)
        toa = struct.unpack_from(f'<{type_size}I', d, type_off)
        def S(si):
            off = soa[si]; _, o = uleb(d, off)
            return d[o:d.index(b'\x00', o)].decode('utf-8','replace')
        def T(ti): return S(toa[ti])
        if code_off < len(d):
            data = (d, T); break
        # try next dex (offsets are per-dex)
    if not data:
        print('offset not in any dex'); return
    d, T = data
    regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<6H', d, code_off)
    insns_size <<= 1  # u32 read of u16 field? careful: insns_size is u32 at code_off+12
    # re-read properly: layout u16,u16,u16,u16,u32,u32
    regs, ins, outs, tries = struct.unpack_from('<4H', d, code_off)
    dbg, insns_size = struct.unpack_from('<2I', d, code_off + 8)
    print(f'regs={regs} ins={ins} outs={outs} tries={tries} insns={insns_size} units')
    base = code_off + 16
    toff = base + insns_size * 2
    if insns_size % 2:
        toff += 2
    handlers_base = toff + tries * 8
    list_size, hoff = uleb(d, handlers_base)
    print(f'handler list size={list_size}')
    for i in range(tries):
        su, sp, ho = struct.unpack_from('<3H', d, toff + i * 8)
        # NOTE: handler_off is relative to the START of the encoded_catch_handler_list
        hp = handlers_base + ho
        n, hp2 = sleb(d, hp)
        rows = []
        catch_all = None
        cnt = n if n > 0 else -n
        p = hp2
        for _ in range(cnt):
            ti, p = uleb(d, p)
            ad, p = uleb(d, p)
            rows.append((T(ti), ad))
        if n <= 0:
            catch_all, p = uleb(d, p)
        print(f'TRY [{su*2:#06x}..{(su+sp)*2:#06x}) ->')
        for (ty, ad) in rows:
            print(f'    catch {ty} -> {ad*2:#06x}')
        if catch_all is not None:
            print(f'    catch-all -> {catch_all*2:#06x}')

if __name__ == '__main__':
    main()
