#!/usr/bin/env python3
"""S104: brute-force parse packed-switch payload from raw code bytes."""
import struct, sys, zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

APK = "/home/z/my-project/run/s99/apks/com.vayunmathur.games.solitaire.apk"
TARGET = "Lkotlin/text/MatcherMatchResult;"

zf = zipfile.ZipFile(APK)
for name in sorted(n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")):
    d = DEX(zf.read(name))
    for c in d.get_classes():
        if c.get_name() != TARGET:
            continue
        for m in c.get_methods():
            if m.get_name() != "<init>" or m.get_descriptor() != "(Landroidx/savedstate/internal/SavedStateRegistryImpl; B)V":
                continue
            code = m.get_code()
            bc = code.get_bc()
            # try to get raw bytecode
            raw = None
            for attr in ("get_raw", "raw"):
                if hasattr(bc, attr):
                    raw = getattr(bc, attr)
            insns = None
            for attr in ("get_insns", "insns", "get_raw"):
                if hasattr(bc, attr):
                    v = getattr(bc, attr)
                    insns = v() if callable(v) else v
                    if insns:
                        break
            if insns is None:
                # last resort: assemble from instruction op values
                parts = []
                for ins in bc.get_instructions():
                    ov = ins.get_op_value()
                    parts.append(ov if isinstance(ov, bytes) else struct.pack("<H", ov))
                insns = b"".join(parts)
            # insns is a byte array in androguard
            try:
                blob = bytes(insns)
            except Exception:
                blob = bytes(bytearray(insns))
            print("code bytes:", len(blob))
            # scan for packed-switch-payload ident 0x0100 little-endian
            i = 0
            while i + 4 <= len(blob):
                ident = struct.unpack_from("<H", blob, i)[0]
                if ident == 0x0100:
                    size, first_key = struct.unpack_from("<HH", blob, i + 2)
                    tgts = struct.unpack_from(f"<{size}h", blob, i + 6)
                    print(f"packed-switch-payload @byte{i}: size={size} first_key={first_key} targets={tgts}")
                    i += 4 + size * 2
                    continue
                if ident == 0x0200:
                    size = struct.unpack_from("<H", blob, i + 2)[0]
                    print(f"sparse-switch-payload @byte{i}: size={size}")
                    i += 4 + size * 4
                    continue
                i += 2
