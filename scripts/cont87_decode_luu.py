#!/usr/bin/env python3
"""CONT-87 Track 1 (F-NEW-395): decode Luu;.<clinit> try ranges + handler
from org.andstatus.game2048_47.apk. Fixture-first evidence for the
deferred-exception-inside-clinit handler-match gap."""
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = "upload/cont73_apks/org.andstatus.game2048_47.apk"
a = APK(APK_PATH)
found = False
for dex_name in a.get_dex_names():
    raw = a.get_file(dex_name)
    d = DEX(raw)
    for cls in d.get_classes():
        for m in cls.get_methods():
            if m.get_class_name() != "Luu;" or m.get_name() != "<clinit>":
                continue
            found = True
            code = m.get_code()
            print("method Luu;.<clinit> found dex=%s" % dex_name)
            print("registers=%d ins=%d outs=%d" % (
                code.get_registers_size(), code.get_ins_size(),
                code.get_outs_size()))
            print("-- tries --")
            for t in code.get_tries():
                print("  try start=%d count=%d handler_off=%d" % (
                    t.get_start_addr(), t.get_insn_count(),
                    t.get_handler_off()))
            print("-- handlers --")
            for h in code.get_handlers():
                print("  handler off=%s" % h.get_off())
                for ty, addr in h.get_pairs_type_addr():
                    print("    catch %s -> 0x%x (%d)" % (ty, addr, addr))
                ca = h.get_catch_all_addr()
                if ca is not None:
                    print("    catch-all -> 0x%x (%d)" % (ca, ca))
            print("-- bytecode --")
            idx = 0
            for ins in code.get_bc().get_instructions():
                if idx <= 44:
                    print("  pc=%3d %s len=%d" % (
                        idx, ins.get_name(), ins.get_length()))
                idx += ins.get_length()
if not found:
    print("Luu;.<clinit> NOT FOUND")
