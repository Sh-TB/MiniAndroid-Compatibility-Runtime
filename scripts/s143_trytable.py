#!/usr/bin/env python3
"""s143_trytable.py — decode the try/handler tables of initNativeLibs and
loadFromZip (forkgram classes.dex) with exact dex layout:

  code_item: registers u16, ins u16, outs u16, tries u16, debug u32,
             insns_size u32, insns[], padding to 4, try_item[tries] (8B:
             start_addr u32, insn_count u16, handler_off u16),
             encoded_catch_handler_list (size uleb, handlers...).

  encoded_catch_handler: size sleb (negative => catch_all present),
             [typed handlers: type_idx uleb + addr uleb]..., catch_all_addr
             uleb if size<=0.
Handler offsets are RELATIVE to the handler list base.
"""
import zipfile, importlib.util, struct, sys

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

z = zipfile.ZipFile('/home/z/my-project/upload/tg/forkgram.apk')
d = cd.Dex(z.read('classes.dex'))
off = d.find_class('Lorg/telegram/messenger/NativeLoader;')
cm = d.class_methods(off)


def uleb(o):
    r = s = 0
    while True:
        b = d.b[o]; o += 1
        r |= (b & 0x7f) << s
        if not b & 0x80:
            return r, o
        s += 7


def sleb(o):
    r = s = 0
    while True:
        b = d.b[o]; o += 1
        r |= (b & 0x7f) << s
        s += 7
        if not b & 0x80:
            if b & 0x40:
                r -= (1 << s)
            return r, o


for m in cm['direct'] + cm['virtual']:
    if m[0] not in ('initNativeLibs', 'loadFromZip'):
        continue
    code = m[4]
    tries = d.u(code + 6, 2)
    insns = d.u(code + 12, 4)
    toff = code + 16 + insns * 2
    if toff % 4:
        toff += 2
    hsize, hp = uleb(toff + tries * 8)  # handler list size + base
    print(f"== {m[0]}: insns={insns} tries={tries} handler_list_size={hsize}")
    for t in range(tries):
        su, cnt, hoff = struct.unpack_from('<IHH', d.b, toff + t * 8)
        # handler_off is relative to the START of the handler list
        base = toff + tries * 8
        p = base
        # walk hsize uleb to get base of handlers
        sz, q = uleb(base)
        p = q + hoff
        n, p = sleb(p)
        hs = []
        catch_all = None
        if n >= 0:
            for i in range(n):
                ti, p = uleb(p)
                ad, p = uleb(p)
                hs.append((d.type_str(ti), ad))
        else:
            for i in range(-n):
                ti, p = uleb(p)
                ad, p = uleb(p)
                hs.append((d.type_str(ti), ad))
            catch_all, p = uleb(p)
        print(f"  try [{su:#x}..{su+cnt:#x}) handlers={hs}"
              + (f" catch_all={catch_all:#x}" if catch_all is not None else ""))
