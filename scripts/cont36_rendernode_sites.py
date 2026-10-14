#!/usr/bin/env python3
"""CONT-36: find every drawRenderNode / beginRecording / endRecording call
site in composeStopwatch (fixed scanner) — who SHOULD composite the
RenderNode layers onto the frame canvas."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))
want = ("drawRenderNode", "beginRecording", "endRecording", "setPosition",
        "setClipToBounds")
hits = {}
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                if "invoke" not in ins.get_name():
                    continue
                out = ins.get_output()
                if "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                tm = out.split("->")[1].split(":")[0].split("(")[0]
                if tm in want and ("RenderNode" in tcls or "RecordingCanvas" in tcls):
                    hits.setdefault((tcls, tm), []).append(
                        f"{m.get_class_name()}.{m.get_name()}")
        except Exception:
            continue
for (tc, tm), ms in sorted(hits.items()):
    u = sorted(set(ms))
    print(f"{tc}->{tm}: {len(u)} callers, e.g. {u[:8]}")
