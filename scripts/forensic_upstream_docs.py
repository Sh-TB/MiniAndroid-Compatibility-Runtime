#!/usr/bin/env python3
"""forensic_upstream_docs.py — issue #364 upstream-reuse deliverables.
Generated from verified facts: Makefile link flags, third_party/ contents,
canonical/reuse_registry.json, docs/GRAPHICS_SOURCE_REGISTRY.md, and the
loading/graphics campaign records. No claim beyond what is wired today."""
import json, os, subprocess

D = "/home/z/my-project"
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], cwd=D,
                      capture_output=True, text=True).stdout.strip()[:8]

# ---------------- UPSTREAM_CODE_INVENTORY ----------------
inv = [
 {"component": "QuickJS", "class": "VENDORED", "location": "miniandroid/third_party/quickjs/ (quickjs.c/libregexp/libunicode/libbf/cutils)",
  "version": "2024-01-13 (third_party/quickjs/VERSION)", "license": "MIT",
  "upstream": "https://github.com/bellard/quickjs", "subsystem": "WebView/HTML5 JS engine (S107-S115 line)",
  "runtime_call_path": "webview_engine -> QuickJS eval; Breakout-71 real game loop proven (#353)",
  "update_strategy": "manual vendored snapshot; re-vendor on measured need"},
 {"component": "nlohmann/json", "class": "VENDORED", "location": "miniandroid/third_party/nlohmann_json/include",
  "version": "single-header snapshot", "license": "MIT",
  "upstream": "https://github.com/nlohmann/json", "subsystem": "JSON everywhere (package.json records, traces, registries)",
  "runtime_call_path": "pkgstore records, pkgaudit output, file-IO provenance JSONL",
  "update_strategy": "manual snapshot"},
 {"component": "PortableGL", "class": "VENDORED", "location": "miniandroid/third_party/portablegl/portablegl.h",
  "version": "snapshot", "license": "MIT", "upstream": "https://github.com/rswinkle/PortableGL",
  "subsystem": "software GL (pgl_backend/gles20_bridge)",
  "runtime_call_path": "COMPILED-BUT-ZERO-CALLER at audit time (LOAD-AUDIT census) — honest note: wired into build, not into a measured consumer yet",
  "update_strategy": "keep until GLSurfaceView family (F-NEW-157) lands or drop"},
 {"component": "stb family (stb_image/stb_vorbis) + minimp3", "class": "VENDORED-ADAPTED",
  "location": "miniandroid/third_party/stb/, miniandroid/third_party/audio/{minimp3.h,stb_vorbis.c}",
  "version": "snapshot", "license": "Public Domain / CC0",
  "upstream": "https://github.com/nothings/stb, https://github.com/lieff/minimp3",
  "subsystem": "image decode adaptors + audio codecs; MiniAndroid GIF compositor built ON stb (adapted)",
  "runtime_call_path": "renderer/gif_decoder, audio paths",
  "update_strategy": "snapshot; GIF compositor is in-repo adapted code"},
 {"component": "zlib/libpng/libjpeg/libwebp(+demux)", "class": "HOST-LINKED", "location": "system (Makefile -lz -ljpeg -lwebp -lwebpdemux -lpng)",
  "version": "host distro", "license": "zlib / libpng / IJG-BSD / BSD-3",
  "subsystem": "PNG/JPEG/WebP decode for BitmapFactory + renderer",
  "runtime_call_path": "BitmapFactory decode* paths (decodeStream/decodeFile verified by probe 23/23)",
  "update_strategy": "host-managed"},
 {"component": "SQLite", "class": "HOST-LINKED", "location": "system (-lsqlite3)",
  "license": "Public Domain", "subsystem": "database shadow (storage/sqlite_shadow)",
  "runtime_call_path": "SQLiteDatabase family; real WAL pragma + single databases_dir verified (probe: WAL/db persisted on store)",
  "update_strategy": "host-managed"},
 {"component": "OpenSSL (libssl/libcrypto)", "class": "HOST-LINKED", "location": "system (-lssl -lcrypto)",
  "license": "Apache-2.0", "subsystem": "TLS substrate for the MiniAndroid HTTP(S) client (adapted, libcore luni semantics)",
  "runtime_call_path": "S100 Mini Browser real HTTPS GET + 307 redirect (E5, canonical GIFs)",
  "update_strategy": "host-managed; VERIFY_NONE transport deviation recorded"},
 {"component": "FreeType / HarfBuzz / FriBidi", "class": "HOST-LINKED", "location": "system (-lfreetype -lharfbuzz -lfribidi)",
  "license": "FTL/GPL-2.0 dual / MIT / LGPL-2.1+", "subsystem": "fonts/text shaping (fonts/text_shaper; S132 text laws)",
  "runtime_call_path": "TextView/paint text path; glyph consumption proven by text-bearing goldens",
  "update_strategy": "host-managed"},
 {"component": "mpg123 / libsndfile", "class": "HOST-LINKED", "location": "system (-lmpg123 -lsndfile)",
  "license": "LGPL-2.1 / LGPL-2.1", "subsystem": "audio decode (SoundPool/MediaPlayer frontier)",
  "runtime_call_path": "audio_engine (compiled; consumer proof pending — ST frontier)",
  "update_strategy": "host-managed"},
 {"component": "AOSP-derived semantic ports (in-repo code)", "class": "AOSP-PORTED",
  "location": "miniandroid/src/{storage/data_root,res,framework,dex}/... with AOSP citations in comments",
  "license": "Apache-2.0 (AOSP) — attribution in source headers/docs",
  "upstream": "https://android.googlesource.com/platform/frameworks/base + libcore",
  "subsystem": "path/category law (ContextImpl), AssetManager2 open/list/openFd semantics, SharedPreferencesImpl atomic tmp+rename+escape, ActivityThread handleBindApplication provider-install law, LinearLayout/TableLayout weight pass (F-NEW-228), collection/ArrayDeque/UTF-16 laws (ROOT-064..067), sepolicy appdomain device-node law (/dev/urandom)",
  "runtime_call_path": "engine-wide; probe 23/23 + goldens x3",
  "update_strategy": "law-pinned to AOSP source; re-derive on semantic drift"},
 {"component": "GRAPHICS_SOURCE_REGISTRY candidates", "class": "REGISTRY",
  "location": "docs/GRAPHICS_SOURCE_REGISTRY.md (127 entries / 122 repos / 48 evidenced laws)",
  "license": "mixed (per entry)", "subsystem": "graphics/text research registry",
  "runtime_call_path": "reference + decision record; reuse_registry.json is the decision layer",
  "update_strategy": "append-only registry"},
]
with open(f"{D}/docs/UPSTREAM_CODE_INVENTORY.jsonl", "w") as f:
    for r in inv:
        f.write(json.dumps(r) + "\n")

md = ["# UPSTREAM CODE INVENTORY (issue #364)", "",
      f"Generated at HEAD `{HEAD}` from verified facts: Makefile link flags,",
      "`miniandroid/third_party/` contents, `canonical/reuse_registry.json`,",
      "`docs/GRAPHICS_SOURCE_REGISTRY.md`. Classes: VENDORED (in-tree),",
      "HOST-LINKED (system lib), AOSP-PORTED (in-repo adapted code with AOSP",
      "law citations), ADAPTED (wrapper over vendored substrate), REGISTRY.",
      "Citation is not reuse: every row records the runtime call path; rows",
      "whose consumer is not yet measured say so explicitly (PortableGL,", "audio).", "",
      "| Component | Class | License | Runtime call path |", "|---|---|---|---|"]
for r in inv:
    md.append(f"| {r['component']} | {r['class']} | {r.get('license','-')} | {r.get('runtime_call_path','-')[:120]} |")
md += ["", "Machine rows: `docs/UPSTREAM_CODE_INVENTORY.jsonl` (11 rows)."]
open(f"{D}/docs/UPSTREAM_CODE_INVENTORY.md", "w").write("\n".join(md) + "\n")

# ---------------- AVAILABLE_NOT_USED ----------------
notused = [
 {"candidate": "nanoSVG", "url": "https://github.com/memononen/nanosvg", "license": "zlib",
  "verdict": "EVALUATED_NOT_USEFUL_FOR_MEASURED_SUBSET",
  "reason": "S132 measured the app-corpus SVG subset and implemented the needed law in-tree (s132_svg_reader); adopting a full parser would add unmeasured surface."},
 {"candidate": "FFmpeg (libavcodec/libavformat)", "license": "LGPL/GPL",
  "verdict": "NOT_USEFUL_NOW_CORPUS_GATE",
  "reason": "no video corpus need measured; audio already covered by adopted codecs (S132 wave-3 record)."},
 {"candidate": "Wuffs / libnsgif", "verdict": "EVALUATE", "reason": "GIF already served by stb-based in-repo compositor; swap only if fidelity root measured."},
 {"candidate": "resvg", "verdict": "EVALUATE", "reason": "full SVG fidelity beyond measured subset; not triggered."},
 {"candidate": "litehtml / Lexbor", "verdict": "EVALUATE", "reason": "no document-class CSS layout root measured (z.ai CSS 1436 rules handled by S133 record); trigger not fired."},
 {"candidate": "miniz / dr_libs / miniaudio / libcurl / rlottie / tesseract / pixelmatch", "verdict": "EVALUATE-PLANNED",
  "reason": "registry PLANNED/EVALUATE rows: awaiting a measured root (pixelmatch+tesseract planned for visual-diff/OCR tooling)."},
 {"candidate": "SDL2", "verdict": "REJECTED", "reason": "window/event model conflicts with the runtime framebuffer/window shadow laws."},
 {"candidate": "Yoga (flexbox)", "verdict": "REJECTED_FOR_MC041_EXISTING_SUPERIOR",
  "reason": "existing layout interpreter + AOSP weight-pass port covers measured corpus; MC041 decision record."},
 {"candidate": "jadx / androguard / ApkTool / ARSCLib", "verdict": "ORACLE",
  "reason": "used as ground-truth oracles for DEX/ARSC/AXML verification, not linked into the runtime."},
 {"candidate": "Skia / cdroid / Compose-skiko / Godot / libGDX", "verdict": "REFERENCE_ONLY",
  "reason": "loop/law references recorded in the graphics registry; no code imported."},
]
with open(f"{D}/docs/UPSTREAM_AVAILABLE_NOT_USED.jsonl", "w") as f:
    for r in notused:
        f.write(json.dumps(r) + "\n")

# ---------------- REPLACEMENT_PLAN ----------------
plan = [
 {"id": "UPP-001", "area": "dlopen/JNI native libraries (S-2)", "current": "no native .so loading; NDK libs unexercised",
  "plan": "adopt a minimal ELF/dynamic-loader path or bridge to host dlopen with ABI selection; AOSP RuntimeInfo + android_dlopen_ext semantics",
  "fanout": "any app with lib/<abi>/*.so", "status": "PENDING"},
 {"id": "UPP-002", "area": "content:// query/Cursor + FileProvider (S-4)", "current": "provider install stage landed; query/Cursor not",
  "plan": "port ContentProvider query contract + Cursor window semantics from AOSP; FileProvider after", "status": "PENDING"},
 {"id": "UPP-003", "area": "split APKs (S-11)", "current": "base-only", "plan": "base+config split merge at install (AOSP SplitApkVerifier law)", "status": "PENDING"},
 {"id": "UPP-004", "area": "resource config/density/font selection (SELECTION_FROZEN)", "current": "first-config fallback; density 420 hard-coded",
  "plan": "AOSP ResourceTypes config-selection law port + density buckets", "fanout": "all density/night/land resources", "status": "PENDING"},
 {"id": "UPP-005", "area": "Compose runtime", "current": "frontier roots recorded (S102-B LocalDensity, recomposer host)",
  "plan": "upstream AndroidX compose source as ORACLE; implement host hooks only where measured", "status": "PENDING"},
 {"id": "UPP-006", "area": "Broadcasts/Services deep legs (S-3/S-13)", "plan": "AOSP ActiveServices semantics port", "status": "PENDING"},
 {"id": "UPP-007", "area": "sqlite/font provenance traces (ST-10)", "plan": "extend provenance JSONL to sqlite+font consumers", "status": "PENDING"},
]
with open(f"{D}/docs/UPSTREAM_REPLACEMENT_PLAN.jsonl", "w") as f:
    for r in plan:
        f.write(json.dumps(r) + "\n")

# ---------------- LICENSE MATRIX ----------------
lic = [
 {"component": "MiniAndroid (this repo)", "license": "MIT", "attribution": "README", "risk": "none"},
 {"component": "QuickJS", "license": "MIT", "attribution": "third_party/quickjs/LICENSE", "risk": "low"},
 {"component": "nlohmann/json", "license": "MIT", "attribution": "embedded headers", "risk": "low"},
 {"component": "PortableGL", "license": "MIT", "attribution": "upstream header", "risk": "low"},
 {"component": "stb/minimp3/stb_vorbis", "license": "PD/CC0", "attribution": "public domain", "risk": "none"},
 {"component": "zlib", "license": "zlib", "attribution": "host system", "risk": "none"},
 {"component": "libpng", "license": "libpng-2.0", "attribution": "host system", "risk": "none"},
 {"component": "libjpeg-turbo", "license": "IJG/BSD-3", "attribution": "host system", "risk": "none"},
 {"component": "libwebp", "license": "BSD-3", "attribution": "host system", "risk": "none"},
 {"component": "SQLite", "license": "Public Domain", "attribution": "host system", "risk": "none"},
 {"component": "OpenSSL", "license": "Apache-2.0", "attribution": "host system", "risk": "low (advertise-with-notice)"},
 {"component": "FreeType", "license": "FTL/GPL-2.0 dual", "attribution": "host system; FTL notice", "risk": "low"},
 {"component": "HarfBuzz", "license": "MIT (Old MIT)", "attribution": "host system", "risk": "none"},
 {"component": "FriBidi", "license": "LGPL-2.1+", "attribution": "host system, dynamically linked", "risk": "low"},
 {"component": "mpg123", "license": "LGPL-2.1", "attribution": "host system, dynamically linked", "risk": "low"},
 {"component": "libsndfile", "license": "LGPL-2.1", "attribution": "host system, dynamically linked", "risk": "low"},
 {"component": "AOSP-derived ported code", "license": "Apache-2.0", "attribution": "per-file law citations + docs/REAL_ANDROID_LOADING_ORACLE.md", "risk": "low (NOTICE required at release)"},
]
with open(f"{D}/docs/UPSTREAM_LICENSE_MATRIX.jsonl", "w") as f:
    for r in lic:
        f.write(json.dumps(r) + "\n")

# ---------------- RUNTIME USAGE ----------------
usage = [
 {"component": "QuickJS", "measured_consumer": "Breakout-71 HTML5 game loop (#353, E4/E5)", "status": "PROVEN"},
 {"component": "nlohmann/json", "measured_consumer": "pkgstore/pkgaudit/provenance JSONL (probe 23/23)", "status": "PROVEN"},
 {"component": "zlib/libpng/libjpeg/libwebp", "measured_consumer": "BitmapFactory decode paths; AFD bytes == entry bytes (probe)", "status": "PROVEN"},
 {"component": "SQLite", "measured_consumer": "probe WAL/db persistence on store; cache4.db telegram record", "status": "PROVEN"},
 {"component": "OpenSSL", "measured_consumer": "S100 browser HTTPS GET + 307 (E5)", "status": "PROVEN"},
 {"component": "FreeType/HarfBuzz/FriBidi", "measured_consumer": "text-bearing goldens (opencalc/unote/chess x3 byte-identical)", "status": "PROVEN"},
 {"component": "PortableGL", "measured_consumer": "NONE (compiled-but-zero-caller, LOAD-AUDIT census)", "status": "WIRED_NOT_CONSUMED"},
 {"component": "mpg123/libsndfile", "measured_consumer": "NONE yet (audio consumer proof pending ST)", "status": "WIRED_NOT_CONSUMED"},
 {"component": "stb_image/GIF compositor", "measured_consumer": "GIF disposal OBSERVED rows (MG-214..216)", "status": "OBSERVED"},
]
with open(f"{D}/docs/UPSTREAM_RUNTIME_USAGE.jsonl", "w") as f:
    for r in usage:
        f.write(json.dumps(r) + "\n")

# ---------------- UPDATE TRACKING ----------------
upd = [
 {"component": "QuickJS", "vendored_version": "2024-01-13", "upstream_latest": "2025 snapshot exists",
  "strategy": "re-vendor only on a measured JS-compat root; frozen until then", "next_check": "on S-10/WebView root"},
 {"component": "nlohmann/json", "strategy": "API-stable; update optional", "next_check": "annual"},
 {"component": "PortableGL", "strategy": "keep-or-drop decision tied to F-NEW-157 GLSurfaceView family", "next_check": "on F-NEW-157 attack"},
 {"component": "HOST-LINKED libs", "strategy": "host distro manages versions; CI rebuild law keeps compatibility", "next_check": "per build"},
 {"component": "AOSP ports", "strategy": "law-pinned to AOSP branch heads cited in source; re-derive on semantic drift (e.g. RES_TABLE_ENTRY Compact law S127)", "next_check": "per campaign"},
]
with open(f"{D}/docs/UPSTREAM_UPDATE_TRACKING.jsonl", "w") as f:
    for r in upd:
        f.write(json.dumps(r) + "\n")

print("upstream docs written:",
      sum(os.path.exists(f"{D}/docs/UPSTREAM_{n}.{e}")
          for n in ("CODE_INVENTORY", "AVAILABLE_NOT_USED", "REPLACEMENT_PLAN",
                    "LICENSE_MATRIX", "RUNTIME_USAGE", "UPDATE_TRACKING")
          for e in (("md", "jsonl") if n == "CODE_INVENTORY" else ("jsonl",))))
