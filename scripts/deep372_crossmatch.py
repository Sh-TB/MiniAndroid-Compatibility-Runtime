#!/usr/bin/env python3
"""deep372_crossmatch.py — issue #372 candidate cross-match (no-duplicate law).

For each externally-researched deep root-cause candidate (#372 header list),
classify against the existing root registry + current implementation:
  A DUPLICATE | B SAME_ROOT/NEW_EVIDENCE | C NEW_SUB_LAW | D NEW_ROOT |
  E NOT_APPLICABLE | F EXTERNAL/FUTURE_BOUNDARY
Only C/D may create runtime work. Output: docs/DEEP_ROOT_CROSSMATCH.jsonl
"""
import json
from pathlib import Path

BASE = Path("/home/z/my-project")
reg = json.load(open(BASE / "root_registry.json"))
roots = reg["roots"]


def reg_hits(keywords):
    out = []
    for r in roots:
        blob = json.dumps(r).lower()
        if any(k in blob for k in keywords):
            out.append(f"{r.get('id')} ({r.get('status')})")
    return out[:4]


candidates = [
    {"candidate": "gralloc usage-dependent buffer allocation",
     "keywords": ["gralloc", "buffer usage", "allocator"],
     "classification": "E NOT APPLICABLE",
     "reason": "MiniAndroid renders through a host software framebuffer (1080x1920 RGBA); there is no gralloc/HWC layer to mis-allocate. The analogous contract (bitmap config + stride handling) is covered by the bitmap/canvas shadows.",
     "registry": reg_hits(["gralloc"]),
     "work": None},
    {"candidate": "synchronization fences / back-pressure",
     "keywords": ["fence", "back-pressure", "backpressure"],
     "classification": "E NOT APPLICABLE",
     "reason": "Deterministic single-threaded virtual-clock frame pump (F-NEW-232/233); no producer/consumer fence surface exists. Back-pressure cannot arise where frames are pump-ordered.",
     "registry": reg_hits(["fence"]),
     "work": None},
    {"candidate": "composition/transaction commit (SurfaceFlinger)",
     "keywords": ["surfaceflinger", "composition", "transaction"],
     "classification": "E NOT APPLICABLE",
     "reason": "No compositor process; the renderer draws straight to the output frame. Composition contracts reduce to the canvas/ViewTree draw order laws already covered (TouchDispatcher claim law, draw-op census).",
     "registry": reg_hits(["surfaceflinger"]),
     "work": None},
    {"candidate": "ABI advertisement vs actual execution/translation truth",
     "keywords": ["abi", "native bridge", "arm64", "supported_abis"],
     "classification": "D NEW ROOT",
     "reason": "REAL and proven this wave: advertised ABIs (arm64-v8a/armeabi) are extraction-only; executable ABI is x86_64. Redroid-class live proof: arm64-only APK installs, launch cannot reach engine (EggReturnsHome). Implemented as the prerequisite layer + environment profile.",
     "registry": reg_hits(["supported_abis", "abi law", "native execution"]),
     "work": "R-NEW-465 IMPLEMENTED+TESTED (pkginspect prerequisites; docs/ENVIRONMENT_PROFILE.json); CPU translation remains F EXTERNAL/FUTURE_BOUNDARY (quantified: 2/30 corpus APKs blocked)"},
    {"candidate": "linker namespace / DT_NEEDED closure",
     "keywords": ["linker", "dt_needed", "namespace"],
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "reason": "The S-2 native-execution wave (dlopen/JNI_OnLoad/dlsym + honest ULE shapes) already answers the linker surface for the host-executable ABI; pkginspect libs section reports ELF validity/soname/JNI exports per entry (DT_NEEDED-level truth per lib).",
     "registry": reg_hits(["dlopen", "s-2", "linker", "elf"]),
     "work": None},
    {"candidate": "Binder / system-service availability",
     "keywords": ["binder", "servicemanager", "system service", "activeservices"],
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "reason": "#370 B5 wave: ActiveServices started-vs-bound lifecycle, registerReceiver/sendBroadcast delivery, IntentFilter engine state, SVC-01..04/BCAST-01..04 probes; getPackageInfo(GET_PROVIDERS)/resolveContentProvider laws. The host runtime models services in-process by design — Binder IPC as such is E (no multi-process), the SERVICE SEMANTICS are covered.",
     "registry": reg_hits(["activeservices", "broadcast", "service lifecycle"]),
     "work": None},
    {"candidate": "RRO/idmap/resource mutation",
     "keywords": ["rro", "idmap", "overlay"],
     "classification": "E NOT APPLICABLE",
     "reason": "No Runtime Resource Overlay runtime exists or is advertised; resource resolution is ARSC-native (density best-match, -night/-land unreachable-at-frozen-profile law CFG-01..05). Apps shipping overlay-affected resources would see the base table — an honest documented boundary.",
     "registry": reg_hits(["idmap", "overlay", "arsc"]),
     "work": None},
    {"candidate": "display/surface identity",
     "keywords": ["surfaceview", "surface", "display identity"],
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "reason": "SurfaceView/GL-surface shadows (gl_surface_shadow, surface_view_shadow) + window-background/window-root laws (F-NEW-233 census, EXP092 window-background resolve) cover the surface identity surface MiniAndroid exposes.",
     "registry": reg_hits(["surface_view", "windowbackground", "window root"]),
     "work": None},
    {"candidate": "colorspace/premultiplication",
     "keywords": ["premulti", "colorspace", "bitmap config"],
     "classification": "C NEW_SUB_LAW (candidate, not yet divergent)",
     "reason": "Bitmap provenance waves proved decode→draw byte-truth for PNG/JPEG/GIF/WebP (flappycow 12 events, dimensions match APK art). No current first divergence implicates alpha-premultiply or colorspace conversion. Registered as a WATCH candidate; only a real divergence creates work.",
     "registry": reg_hits(["premulti", "bitmap provenance", "decode"]),
     "work": "None (no divergence — do not implement without evidence)"},
    {"candidate": "white/black from prerequisite mismatch (WS-002)",
     "keywords": ["white screen", "window root", "compose", "fragment"],
     "classification": "B SAME_ROOT/NEW_EVIDENCE",
     "reason": "WS audit this wave: 8 classified cases — 5 ordinary runtime roots (ViewTree/Compose/Fragment/WindowInsets), 2 environment-caused/dual (ARM-only native, Vulkan-on-GLES2), 1 recorded duplicate. Prerequisite layer distinguishes them machine-readably per APK.",
     "registry": reg_hits(["f-new-197", "white-screen", "f-new-162"]),
     "work": "R-NEW-465 evidence; runtime roots stay under their registered IDs (F-NEW-197 family)"},
]

rows = []
for c in candidates:
    rows.append({
        "candidate": c["candidate"],
        "classification": c["classification"],
        "reason": c["reason"],
        "registry_crossmatch": c["registry"],
        "runtime_work": c["work"],
    })

with open(BASE / "docs/DEEP_ROOT_CROSSMATCH.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print("wrote docs/DEEP_ROOT_CROSSMATCH.jsonl —", len(rows), "candidates")
from collections import Counter
print(Counter(r["classification"].split()[0] for r in rows))
