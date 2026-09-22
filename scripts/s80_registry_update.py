#!/usr/bin/env python3
"""s80_registry_update.py — S80 registry additions via the canonical
generator (S24 law: fix the generator, never hand-patch derived output).

Adds:
  R-NEW-401  Context.getExternalCacheDir → File bridge (Telegram-class
             storage-init chain; ImageLoader pc=289 null-File NPE family).
"""
import json

P = "/home/z/my-project/root_registry.json"

NEW = [
    {
        "id": "R-NEW-401",
        "title": "Context.getExternalCacheDir → File bridge: external storage emulated as AVAILABLE (mirrors getExternalFilesDir P1.7)",
        "status": "USED_BY_EXECUTION",
        "priority": "P2",
        "evidence": (
            "UPSTREAM: ContextImpl.getExternalCacheDir() returns the external "
            "cache dir, null only when external storage is unavailable — the "
            "runtime emulates it as available, consistent with the P1.7 "
            "getExternalFilesDir bridge. OBSERVED GAP: Telegram v12 "
            "ImageLoader.<init> pc=289 dereferences a null File receiver "
            "(14 in-flight exceptions, blank shell render, load frontier "
            "#16 family). FIX: bridge returns the canonical File singleton "
            "for Context/Activity/Application/Service receivers. POST: "
            "engine rebuilt; golden battery 26/26 rc=0, verifier 26/26 SAME, "
            "fidelity BYTE-IDENTICAL 90/90 (zero golden-path deltas). "
            "NEXT_PROBE: Telegram ImageLoader pc=289 still resolves a null "
            "File from its own static chain (ApplicationLoader context "
            "wiring) — disasm of ImageLoader.<init> queued; the remaining "
            "REC-MISS cluster (SparseArray.<init> x33, "
            "SharedPreferences.getBoolean/getInt x24, ThreadLocal.<init>, "
            "WeakReference.get) recorded as the next bridge wave."
        ),
        "added": "S80",
    },
]

with open(P) as f:
    d = json.load(f)

have = {r["id"] for r in d["roots"]}
for rec in NEW:
    if rec["id"] not in have:
        d["roots"].append(rec)
        d["total"] = len(d["roots"])

d["note"] = (
    d.get("note", "") + " | S80: three real games (Snake Deluxe, Mini Tetris, "
    "2048) built + played on the runtime; R-NEW-401 external-cache bridge."
).strip(" |")

with open(P, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print("registry roots:", d["total"])
