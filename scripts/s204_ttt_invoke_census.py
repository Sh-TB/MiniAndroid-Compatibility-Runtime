#!/usr/bin/env python3
"""S204 — enumerate board-class methods via the in-tree DexFile dumper and
census the gdx/GL methods each invokes (from invoke-kind bytecode sites)."""
import sys, zipfile

sys.path.insert(0, "/home/z/my-project/miniandroid/tools")
import dump_method_bytecode as d  # noqa

APK = '/home/z/my-project/upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk'
CLASSES = {"Lcom/emmanuelmess/tictactoe/DrawableShape;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeRenderer;",
           "Lcom/emmanuelmess/tictactoe/OActor;",
           "Lcom/emmanuelmess/tictactoe/XActor;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeText;",
           "Lcom/emmanuelmess/tictactoe/XOText;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeGame;",
           "Lcom/emmanuelmess/tictactoe/TicTacToeGameKt;"}

INVOKE_OPS = {0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78}

with zipfile.ZipFile(APK) as z:
    data = z.read('classes.dex')

dex = d.DexFile(data, 'classes.dex')
for cls in dex.classes:
    if cls['desc'] not in CLASSES:
        continue
    print(f"\n=== {cls['desc']} ===")
    for kind in ("direct_methods", "virtual_methods"):
        for m in cls["methods"].get(kind, []):
            name = dex.get_method_name(m["method_idx"])
            desc = dex.get_method_descriptor(m["method_idx"])
            code_off = m["code_off"]
            if not code_off:
                print(f"  {desc}  [no code]")
                continue
            insns_size = dex._u32(code_off + 12)
            insns_off = code_off + 16
            calls = []
            pc = 0
            while pc < insns_size:
                op_off = insns_off + pc * 2
                op = dex.data[op_off] | (dex.data[op_off + 1] << 8)
                op_low = op & 0xFF
                size = d.get_size(op_low, dex.data, op_off)
                if op_low in INVOKE_OPS and size >= 3:
                    midx = dex.data[op_off + 2] | (dex.data[op_off + 3] << 8)
                    got = dex.get_method_descriptor(midx)
                    full = f"{got[0]}->{got[1]}" if isinstance(got, tuple) else str(got)
                    # keep only gdx/GL/app targets
                    if any(t in full for t in (
                            "badlogic", "opengl", "emmanuelmess", "Gdx2D")):
                        calls.append(full)
                pc += size
            tag = 'D' if kind.startswith('direct') else 'V'
            print(f"  [{tag}] {desc}")
            for c in calls:
                print(f"        -> {c}")
