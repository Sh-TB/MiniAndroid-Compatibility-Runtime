#!/usr/bin/env python3
"""cont70 ANT-1 decode v2 — read the encoded_catch_handler_list directly from
the DEX map (androguard TryItem carries only handler_off). Print the try
range, typed catches, catch-all, and pc=67 coverage for
CoordinatorLayout.getResolvedLayoutParams."""
import logging
import struct
import zipfile

logging.disable(logging.CRITICAL)
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk"
CLS = "Landroidx/coordinatorlayout/widget/CoordinatorLayout;"
METH = "getResolvedLayoutParams"

z = zipfile.ZipFile(APK)
for n in sorted(z.namelist()):
    if not (n.startswith("classes") and n.endswith(".dex")):
        continue
    raw = z.read(n)
    dx = DEX(raw)
    for c in list(dx.get_classes()):
        if c.get_name() != CLS:
            continue
        for m in list(c.get_methods()):
            if m.get_name() != METH:
                continue
            code = m.get_code()
            print(f"{n}: {CLS}.{METH} tries={len(code.tries)}")
            for t in code.tries:
                start = t.get_start_addr()
                end = start + t.get_insn_count()
                hoff = t.get_handler_off()
                print(f"  try [{start:#x}..{end:#x}) handler_off={hoff:#x} covers_pc67={start <= 67 < end}")
            # encoded_catch_handler_list lives right after the tries in the
            # code_item: tries_size*8 bytes of TryItem, then the handler list.
            # Parse it manually per the DEX spec.
            # code_item layout: registers_size u2, ins_size u2, outs_size u2,
            # tries_size u2, debug_info_off u4, insns_size u4, insns[],
            # padding u2 (if odd), tries[], handlers[]
            buf = code  # androguard stores the raw code item; use get_raw? Use CM offsets instead.
            # Simpler: androguard exposes the handler list via the DEX class.
            # Fall back to manual parse from m.get_code().offset.
            off = code.get_off()
            regs, insz, outz, tries_size, dbg, insns_size = struct.unpack_from("<HHHHII", raw, off)
            insns_start = off + 16
            after_insns = insns_start + insns_size * 2
            if insns_size % 2 == 1:
                after_insns += 2
            tries_start = after_insns
            handlers_start = tries_start + tries_size * 8
            p = handlers_start
            # uleb128 helpers
            def uleb(p):
                r = 0; s = 0
                while True:
                    b = raw[p]; p += 1
                    r |= (b & 0x7F) << s
                    if not (b & 0x80):
                        return r, p
                    s += 7
            list_size, p = uleb(p)
            print(f"  encoded_catch_handler_list size={list_size}")
            for i in range(list_size):
                hsize, p = uleb(p)  # sleb128 but magnitude parse ok for |size|
                raw_size = hsize
                neg = False
                # sleb128 decode
                val = 0; shift = 0
                pp = p
                while True:
                    b = raw[pp]; pp += 1
                    val |= (b & 0x7F) << shift
                    shift += 7
                    if not (b & 0x80):
                        if b & 0x40 and shift < 64:
                            val -= (1 << shift)
                        break
                hsize = val
                npairs = abs(hsize)
                entry_start = pp
                pairs = []
                for _ in range(npairs):
                    tidx, pp = uleb(pp)
                    addr, pp = uleb(pp)
                    desc = dx.get_cm().get_type(tidx) if hasattr(dx, "get_cm") else None
                    pairs.append((tidx, addr, desc))
                catch_all = None
                if hsize <= 0:
                    catch_all, pp = uleb(pp)
                in_list = (hoff + handlers_start) == entry_start
                print(f"  handler#{i} size={hsize} ours={in_list}")
                for tidx, addr, desc in pairs:
                    print(f"     typed {desc} -> @{addr:#x}")
                if catch_all is not None:
                    print(f"     catch-all -> @{catch_all:#x}")
                p = pp
            raise SystemExit
