#!/usr/bin/env python3
"""s131_reuse_first.py — GLOBAL ARCHITECTURAL LAW: REUSE-FIRST.

User law (2026-10): "MAXIMUM REAL-APK COMPATIBILITY WITH MINIMUM NEW CODE".
Before ANY new handwritten subsystem code, a small/mature/maintained/
open-source implementation must be searched and (if suitable) integrated.

This script materializes the law mechanically:
  1. canonical/reuse_registry.json — the REUSE CANDIDATE DATABASE. Every
     candidate carries the 21 mandated fields (REUSE_CANDIDATE .. REASON)
     plus status/evidence/categories.
  2. docs/REUSE_AUDIT_INPUT.md — the INPUT-cluster reuse audit (executed
     BEFORE more handwritten input code, per law §14).
  3. docs/REUSE_EXTERNAL_COMPONENT_MAP.md — the dedicated map section.

The master-worklist generator (s128_build_master_worklist.py) consumes
canonical/reuse_registry.json: it enriches every item with a
`reuse_candidate` field and emits `## 12. REUSE / EXTERNAL COMPONENT MAP`.

Status vocabulary: ADOPTED_WIRED (linked in Makefile/LIBS) · ADOPTED_VENDORED
(third_party/ tree wired) · ADAPTED (vendored + local upstream-bug fixes,
documented) · ORACLE (diff-test oracle, not runtime) · EVALUATE (researched,
integration pending) · PLANNED (decided, not scheduled) · REFERENCE_ONLY
(source of laws; port-by-law, never wholesale) · REJECTED (with reason).
"""
import json
import os

ROOT = "/home/z/my-project"
CANON = f"{ROOT}/canonical"
DOCS = f"{ROOT}/docs"


def cand(cid, name, url, upstream, version, last_update, src_size, bin_size,
         lic, deps, cpu, ram, build_cost, integ_cost, adapter, caps,
         roots_removed, apk_cov, maint, updateab, decision, reason,
         status, categories, evidence):
    return {
        "REUSE_CANDIDATE": cid,
        "name": name,
        "SOURCE_URL": url,
        "UPSTREAM_PROJECT": upstream,
        "VERSION": version,
        "LAST_UPDATE": last_update,
        "SOURCE_SIZE": src_size,
        "BINARY_SIZE_IF_RELEVANT": bin_size,
        "LICENSE": lic,
        "DEPENDENCIES": deps,
        "CPU": cpu,
        "RAM": ram,
        "BUILD_COST": build_cost,
        "INTEGRATION_COST": integ_cost,
        "ADAPTER_SIZE": adapter,
        "CAPABILITIES": caps,
        "ROOTS_ELIMINATED": roots_removed,
        "APK_COVERAGE": apk_cov,
        "MAINTENANCE_STATUS": maint,
        "UPDATEABILITY": updateab,
        "DECISION": decision,
        "REASON": reason,
        "status": status,
        "categories": categories,
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# THE DATABASE. Sizes/licenses are recorded from upstream docs/verified
# packaging; re-verify VERSION/LAST_UPDATE at integration time (law §12).
# ---------------------------------------------------------------------------
CANDIDATES = [
    # ============ ADOPTED & WIRED (evidence = Makefile / source tree) =======
    cand("zlib", "zlib", "https://zlib.net", "madler/zlib (reference mirror)",
         "system 1.3.x", "2024-01 (1.3.1)", "~90k LOC", "linked -lz",
         "zlib", "none", "negligible", "negligible", "system package",
         "0 (already linked)", "0 — linked",
         "DEFLATE/inflate, ZIP entries (stored+deflated), adler32/crc32",
         "the whole APK-container family (MC-001); never hand-write inflate",
         "every APK (universal)", "ACTIVE (development paused at maturity)",
         "STABLE — drop-in updates", "KEEP",
         "Already the runtime's APK container substrate; hand-written inflate would be ~10k LOC of risk for zero gain.",
         "ADOPTED_WIRED", ["MC-001"], "miniandroid/Makefile L24 (-lz)"),
    cand("libpng", "libpng", "http://www.libpng.org/pub/png/libpng.html",
         "pnggroup/libpng", "system 1.6.x", "2024-2025 releases", "~80k LOC",
         "linked -lpng", "PNG-2.0 (permissive)", "zlib", "negligible", "low",
         "system package", "0 (wired UNIFIED_011.1)", "0 — linked",
         "PNG decode incl. tRNS/palette/interlace", "PNG decode family (MC-067)",
         "all image-bearing APKs", "ACTIVE", "STABLE", "KEEP",
         "S94 verified; hand-written PNG decode is forbidden by DO_NOT_REINVENT.",
         "ADOPTED_WIRED", ["MC-064", "MC-067", "MC-080"],
         "miniandroid/Makefile FONTS_LIBS (-lpng)"),
    cand("libjpeg-turbo", "libjpeg-turbo",
         "https://github.com/libjpeg-turbo/libjpeg-turbo",
         "libjpeg-turbo/libjpeg-turbo", "system 2.x/3.x", "active 2025",
         "~250k LOC", "linked -ljpeg", "IJG + BSD-3", "none", "low (SIMD)",
         "low", "system package", "0 — linked", "0",
         "JPEG baseline+progressive decode", "JPEG decode family",
         "all JPEG-bearing APKs", "VERY ACTIVE", "STABLE", "KEEP",
         "Fastest maintained JPEG decoder; S94 CLOSED.",
         "ADOPTED_WIRED", ["MC-064", "MC-067"], "miniandroid/Makefile L24 (-ljpeg)"),
    cand("libwebp", "libwebp (+libwebpdemux)",
         "https://developers.google.com/speed/webp",
         "webmproject/libwebp", "system 1.3/1.4", "active 2024-2025",
         "~110k LOC", "linked -lwebp -lwebpdemux", "BSD-3", "none",
         "medium (VX/NEON paths)", "low", "system package", "0 — linked",
         "0", "WebP lossy/lossless/animated decode",
         "WebP decode family; animated WebP for AnimatedDrawable",
         "image-heavy APKs incl. Telegram", "ACTIVE", "STABLE", "KEEP",
         "Conformance test wave still pending (S94 note); keep library, add tests.",
         "ADOPTED_WIRED", ["MC-064", "MC-067"],
         "miniandroid/Makefile L26 (-lwebp -lwebpdemux)"),
    cand("sqlite3", "SQLite", "https://sqlite.org", "sqlite/sqlite (amalgamation)",
         "system 3.4x (continuous releases, ~6/yr)", "active 2025",
         "~250k LOC amalgamation", "linked -lsqlite3", "PUBLIC DOMAIN",
         "none", "low", "low (page cache configurable)",
         "system package (amalgamation = 2 files)", "0 — linked",
         "shadow only: sqlite_shadow.cpp (~small)",
         "full SQL RDBMS: SQLiteDatabase/SQLiteStatement/Cursor semantics",
         "the entire database family (MC-104); org.telegram.SQLite 20 natives (S108 R-017)",
         "Telegram + any DB-consuming APK", "VERY ACTIVE (oldest maintained lib)",
         "LEGENDARY — amalgamation drop-in", "KEEP",
         "User law §6: DO NOT reinvent SQLite. Real sqlite3 is already the backend (M3 F-ROOM-CHAIN); every future DB root is adapter-level, never engine-level.",
         "ADOPTED_WIRED", ["MC-104", "MC-105"],
         "miniandroid/Makefile L24 (-lsqlite3); src/storage/sqlite_shadow.cpp; S108 ROOT-017"),
    cand("openssl", "OpenSSL (libssl/libcrypto)",
         "https://www.openssl.org", "openssl/openssl",
         "system 3.x", "active 2025", "~700k LOC", "linked -lssl -lcrypto",
         "Apache-2.0", "none", "medium", "medium", "system package",
         "0 — linked (S100 NET-001)", "0 — linked; http_client adapter small",
         "TLS 1.2/1.3, X.509, RNG, hashing — the whole security boundary",
         "hand-written TLS would be un-shippable; MC-109/MC-110/MC-128 roots",
         "every HTTPS APK", "VERY ACTIVE", "STABLE", "KEEP",
         "BoringSSL (AOSP's TLS) is an OpenSSL fork — provenance law satisfied.",
         "ADOPTED_WIRED", ["MC-109", "MC-110", "MC-128"],
         "miniandroid/Makefile L24; src/api/http_client.cpp"),
    cand("mpg123", "mpg123", "https://www.mpg123.de", "mpg123 overlay",
         "system 1.3x", "active", "~60k LOC", "linked -lmpg123", "LGPL-2.1+",
         "none", "low", "low", "system package", "0 — linked", "0",
         "MP1/MP2/MP3 decode", "MP3 audio decode (MC-090)",
         "audio APKs/games", "ACTIVE", "STABLE", "KEEP",
         "Reference-quality maintained MP3 decoder; paired with minimp3 fallback.",
         "ADOPTED_WIRED", ["MC-090"], "miniandroid/Makefile L24 (-lmpg123)"),
    cand("libsndfile", "libsndfile", "https://libsndfile.github.io/libsndfile/",
         "libsndfile/libsndfile", "system 1.2.x", "active", "~90k LOC",
         "linked -lsndfile", "LGPL-2.1+", "none", "low", "low",
         "system package", "0 — linked", "0",
         "WAV/AIFF/FLAC (subset) file audio decode+write",
         "WAV decode family (MC-090)", "audio APKs/games", "ACTIVE", "STABLE",
         "KEEP",
         "WAV/container decode reused; FLAC depth to be checked vs dr_flac at integration.",
         "ADOPTED_WIRED", ["MC-090"], "miniandroid/Makefile L24 (-lsndfile)"),
    cand("freetype", "FreeType", "https://freetype.org", "freetype/freetype",
         "system 2.13.x", "active 2024-2025", "~300k LOC", "linked -lfreetype",
         "FTL/GPL-2.0+exception (permissive)", "zlib, libpng (optional)",
         "low", "low", "system package", "0 — linked",
         "src/fonts/text_shaper.cpp adapter",
         "glyph rasterization, hinting, font file parsing (TTF/OTF/WOFF)",
         "text-rasterization family (MC-074/075); UNREADABLE_TEXT class",
         "every text-rendering APK (universal)", "VERY ACTIVE", "STABLE",
         "KEEP",
         "S94: glyph rasterization must be FreeType; POC (exp101) proven.",
         "ADOPTED_WIRED", ["MC-074", "MC-075", "MC-077"],
         "miniandroid/Makefile FONTS_LIBS; src/fonts/text_shaper.cpp"),
    cand("harfbuzz", "HarfBuzz", "https://harfbuzz.github.io",
         "harfbuzz/harfbuzz", "system 8.x-10.x", "active 2025",
         "~200k LOC", "linked -lharfbuzz", "Old MIT (permissive)",
         "none (freetype optional)", "low", "low", "system package",
         "0 — linked", "hb buffers in text_shaper.cpp",
         "OpenType shaping: ligatures, Arabic/Indic joins, kerning, marks",
         "text-shaping family (MC-076/077) — UNREADABLE_TEXT class",
         "Arabic/Persian/Indic APKs (large corpus share)", "VERY ACTIVE",
         "STABLE — industry standard (Chromium/Android themselves)",
         "KEEP",
         "User law §6 fonts: FreeType+HarfBuzz IS the AOSP text stack lineage.",
         "ADOPTED_WIRED", ["MC-076", "MC-077", "MC-078"],
         "src/fonts/text_shaper.cpp L13-14 (hb.h, hb-ft.h)"),
    cand("fribidi", "FriBidi", "https://github.com/fribidi/fribidi",
         "fribidi/fribidi", "system 1.0.x", "maintained", "~20k LOC",
         "linked -lfribidi", "LGPL-2.1+", "none", "negligible", "negligible",
         "system package", "0 — linked", "bidi pass in text_shaper.cpp",
         "Unicode bidi algorithm (RTL reordering)",
         "RTL text family (MC-077)", "RTL APKs (fa/ar corpus)",
         "STABLE (mature, low-churn)", "STABLE", "KEEP",
         "POC exp101 proven; conformance oracle available.",
         "ADOPTED_WIRED", ["MC-077"], "src/fonts/text_shaper.cpp L15, L318"),
    cand("quickjs", "QuickJS", "https://bellard.org/quickjs/",
         "bellard/quickjs (vendored; quickjs-ng as update path)",
         "2024-01-13 (CONFIG_VERSION)", "vendored snapshot 2024-01-13",
         "~45k LOC C", "built from third_party/quickjs", "MIT",
         "none", "low (bytecode interpreter)", "low (few MB heap typical)",
         "make build (already in QUICKJS_SOURCES)", "0 — wired",
         "src/webview/canvas2d + JSBridge (~existing)",
         "ES2023 JavaScript engine: eval, DOM-event handlers, game loops in JS",
         "WebView/HTML5/JS family (MC-094/095/097/098)",
         "every WebView APK; blockbuster HTML5 battery", "ACTIVE (upstream); quickjs-ng fork very active",
         "GOOD — vendored; ng fork offers drop-in updates", "KEEP",
         "Law §6 JavaScript: never write a JS interpreter. QuickJS = smallest practical mature engine; already wired into the build.",
         "ADOPTED_VENDORED", ["MC-094", "MC-095", "MC-097", "MC-098"],
         "miniandroid/Makefile L59-61 (QUICKJS_SOURCES); third_party/quickjs/VERSION"),
    cand("stb_image", "stb_image", "https://github.com/nothings/stb",
         "nothings/stb", "vendored snapshot", "vendored", "~7k LOC (1 header)",
         "compiled into runtime", "PUBLIC DOMAIN / MIT", "none",
         "negligible", "negligible", "header-only", "0 — wired",
         "2 upstream bug fixes (S106): disposal-2 semantics, two_back OOB",
         "static image decode: PNG/JPEG/BMP/PSD/GIF(static)/…",
         "static-decode fallback family (MC-064/067)",
         "static-image APKs", "STABLE (low churn by design)", "LOW (single-author)",
         "KEEP",
         "Small-footprint fallback decode path; GIF animated path layered on top (S106).",
         "ADAPTED", ["MC-064", "MC-067", "MC-089"],
         "miniandroid/third_party/stb/stb_image.h; S106 upstream-bug laws"),
    cand("gif_s106", "MiniAndroid GIF compositor (stb-based)",
         "miniandroid/src/renderer/gif_decoder.cpp", "in-repo (stb substrate)",
         "S106", "2025 (this repo)", "~1k LOC adapter", "in-runtime",
         "n/a", "stb_image", "negligible", "negligible", "in build", "done",
         "gif_decoder.{h,cpp} (~1k LOC)",
         "GIF89a animated decode: GCE disposal 0/1/2/3, delays, frame store",
         "GIF family (MC-089) — 12 GIF titles measured by S93",
         "12 GIF titles (S93)", "in-repo", "n/a (in-repo)",
         "KEEP + CONFORMANCE-UPGRADE",
         "Reuse-first check executed: wuffs/libnsgif recorded below as the conformance-upgrade path if S93 disposal edge-cases recur; not a from-scratch engine (stb substrate).",
         "ADAPTED", ["MC-089"],
         "src/renderer/gif_decoder.{h,cpp}; S106 MG-214/215/216"),
    cand("minimp3", "minimp3", "https://github.com/lieff/minimp3",
         "lieff/minimp3", "vendored snapshot", "vendored", "~3k LOC (1 header)",
         "in audio_engine", "CC0", "none", "negligible", "negligible",
         "header-only", "0 — wired", "0",
         "MP3 decode fallback (no system lib dependency)",
         "MP3 decode (MC-090)", "audio APKs", "STABLE", "LOW-MEDIUM", "KEEP",
         "Fallback decode path for environments without mpg123.",
         "ADOPTED_VENDORED", ["MC-090"], "miniandroid/third_party/audio/minimp3.h"),
    cand("stb_vorbis", "stb_vorbis", "https://github.com/nothings/stb",
         "nothings/stb", "vendored snapshot", "vendored", "~5k LOC (1 file)",
         "in audio_engine", "PUBLIC DOMAIN / MIT", "none",
         "negligible", "negligible", "header-only", "0 — wired", "0",
         "OGG Vorbis decode", "Vorbis decode (MC-090)", "game audio APKs",
         "STABLE", "LOW (single-author)", "KEEP",
         "Vorbis decode without Xiph dependency chain.",
         "ADOPTED_VENDORED", ["MC-090"], "miniandroid/third_party/audio/stb_vorbis.c"),
    cand("portablegl", "PortableGL", "https://github.com/rswinkle/PortableGL",
         "rswinkle/PortableGL", "vendored 0.9x", "vendored", "~30k LOC (1 header)",
         "in runtime", "MIT", "none", "medium (CPU rasterizer)",
         "medium", "header-only include path", "0 — include path wired", "gl_surface_shadow adapter",
         "CPU OpenGL ES 2/3-class rasterization (GL law frontier R9/R10)",
         "GLSurfaceView/libGDX family (MC-114)", "GL games", "ACTIVE",
         "GOOD", "KEEP",
         "DO_NOT_REINVENT: PortableGL first per graphics decision record.",
         "ADOPTED_VENDORED", ["MC-114"],
         "miniandroid/third_party/portablegl/portablegl.h; Makefile INCLUDES"),
    cand("nlohmann_json", "nlohmann/json", "https://github.com/nlohmann/json",
         "nlohmann/json", "3.11.3 (Makefile fetch)", "2023 (v3.11.3)",
         "~25k LOC (1 header)", "tooling/diagnostics", "MIT", "none",
         "negligible", "low", "header-only (auto-fetch target)", "0", "0",
         "JSON parse/serialize for tooling", "tooling family",
         "n/a (tooling)", "ACTIVE", "STABLE", "KEEP",
         "Host-side tooling standard; not runtime-critical.",
         "ADOPTED_VENDORED", [], "miniandroid/Makefile L77-79,167-173"),
    cand("http_client", "MiniAndroid HTTP(S) client (OpenSSL substrate)",
         "miniandroid/src/api/http_client.cpp",
         "in-repo (libcore laws + OpenSSL substrate)", "S100 NET-001",
         "2025 (this repo)", "~1k LOC adapter", "in-runtime", "n/a",
         "OpenSSL", "negligible", "negligible", "in build", "done",
         "http_client.{h,cpp}",
         "GET + redirects (301/302/303/307/308), chunked, timeouts — libcore HttpURLConnection semantics",
         "HTTP family (MC-109/110)", "networked APKs",
         "in-repo", "n/a", "KEEP + EXTEND-ON-DEMAND",
         "Reuse law check: substrate is OpenSSL (mature), semantics ported from libcore; POST/keep-alive/pooling recorded as the curl-evaluation trigger (below), NOT as new hand-written TLS.",
         "ADAPTED", ["MC-109", "MC-110"], "src/api/http_client.{h,cpp}"),

    # ============ EVALUATE / DECIDED (integration pending) ==================
    cand("wuffs", "Wuffs (gif decoder)", "https://github.com/google/wuffs",
         "google/wuffs", "0.4.x", "active 2024-2025",
         "~5k LOC generated C for gif", "static lib", "Apache-2.0",
         "none", "low", "low", "single generated .c file", "small",
         "drop-in replace of gif_decoder decode core (~200 LOC)",
         "provably-safe GIF decode: exact disposal semantics + fuzz corpus",
         "GIF disposal edge-case family if S93 wave recurs",
         "12 GIF titles", "ACTIVE (Google-maintained)", "GOOD",
         "EVALUATE",
         "Current stb-based compositor is lawful (2 bugs fixed upstream-style); wuffs is the upgrade when conformance gaps are measured. NOT scheduled preemptively — measure first (high-leverage test §9).",
         "EVALUATE", ["MC-089"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md GIF row"),
    cand("libnsgif", "libnsgif", "https://source.netsurf-browser.org/libnsgif/",
         "NetSurf libnsgif", "0.2.x", "maintained", "~2k LOC", "static lib",
         "MIT", "none", "negligible", "negligible", "tiny", "small",
         "same adapter slot as wuffs", "lightweight GIF decode (LZW + disposal)",
         "GIF family alternative", "12 GIF titles", "STABLE (NetSurf)",
         "MEDIUM", "EVALUATE",
         "Smallest GIF decoder; alternative to wuffs if footprint outranks conformance tooling.",
         "EVALUATE", ["MC-089"], "docs/GRAPHICS_DO_NOT_REINVENT.md"),
    cand("nanosvg", "nanoSVG", "https://github.com/memononen/nanosvg",
         "memononen/nanosvg", "snapshot 2022", "LOW CHURN (effectively frozen)",
         "~4k LOC (2 headers)", "in-runtime", "zlib-style permissive",
         "none", "negligible", "negligible", "header-only", "small (~300 LOC adapter)",
         "VectorDrawable/SVG decode slot",
         "SVG tiny-subset rasterization (paths, gradients basic, shapes)",
         "SVG family (MC-093); Telegram SvgHelper frontier (M-07)",
         "Telegram + vector-drawable APKs", "FROZEN (maintained upstream little)",
         "LOW — stable but little movement",
         "EVALUATE-FIRST",
         "Smallest practical SVG rasterizer; unblocks Telegram SvgHelper family with ~4k LOC instead of a full SVG engine. resvg (below) is the fidelity upgrade. Law §2: tiny+embeddable outranks completeness when coverage matches corpus.",
         "EVALUATE", ["MC-093", "MC-008"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md SVG row; M-07"),
    cand("resvg", "resvg", "https://github.com/linebender/resvg",
         "linebender/resvg (ex RazrFalcon)", "0.4x", "active 2025",
         "~60k LOC Rust", "static lib (Rust ABI or c-api)", "MPL-2.0",
         "Rust toolchain or prebuilt c-lib", "medium", "medium",
         "cargo build (or c-api prebuilt)", "medium (c-api binding)",
         "same SVG decode slot", "high-fidelity SVG 1.1 static rendering + golden-PNG suite",
         "SVG family fidelity tier", "Telegram high-fidelity tier",
         "VERY ACTIVE", "GOOD", "EVALUATE",
         "If nanoSVG fidelity fails measured Telegram cases, resvg is the maintained high-fidelity path. Size accepted only for measured need (law §11).",
         "EVALUATE", ["MC-093"], "docs/GRAPHICS_DO_NOT_REINVENT.md"),
    cand("ffmpeg", "FFmpeg (libavcodec/libavformat)",
         "https://ffmpeg.org", "FFmpeg/FFmpeg", "7.x", "active 2025",
         "~1M LOC full; selective-decode builds far smaller",
         "linked -lavcodec -lavformat -lavutil", "LGPL-2.1+ (config-dependent)",
         "zlib; optional x264/x265 (GPL)", "medium (SIMD paths)",
         "medium", "selective configure build", "medium (~500-1000 LOC adapter)",
         "VideoDrawable/MediaPlayer decode slot",
         "H.264/H.265/VP9/AV1 decode + demux MP4/WebM/MKV",
         "video family (MC-091) + M-02 mandate; CAP-VIDEO-170..174",
         "every video APK (blockbuster-class)", "VERY ACTIVE",
         "STABLE — industry standard", "INTEGRATE-SELECTIVE",
         "Law §6 video + §11: large accepted BECAUSE leverage is massive — one integration closes MC-091 (5 items), M-02, and the autoplay/video game class; selective configure keeps binary small. Never write our own H.264.",
         "PLANNED", ["MC-091"], "M-02; CAP-VIDEO-170..174"),
    cand("litehtml", "litehtml", "https://github.com/litehtml/litehtml",
         "litehtml/litehtml", "0.6/0.9 line", "maintained", "~30k LOC C++",
         "static lib", "BSD-3", "none (containers only)", "low", "low",
         "cmake simple", "medium (html_host + QuickJS glue already available)",
         "replaces src/webview/html_dom layout core (~swap-in)",
         "HTML4/5 subset + CSS2.1/3-subset layout engine (no JS — pairs with QuickJS)",
         "WebView/HTML5 family (MC-094/095/098) + M-16 decision",
         "every WebView APK", "ACTIVE", "GOOD",
         "EVALUATE-FIRST",
         "Law §6 HTML5: never write a browser. Current hand-rolled html_dom is the measured baseline; litehtml+QuickJS is the smallest practical mature PAIR (layout+script) vs chromium-level integration. Decision gate M-16 must run the high-leverage test (§9) with real WebView APKs before new html_dom code.",
         "EVALUATE", ["MC-094", "MC-095", "MC-098"], "M-16"),
    cand("lexbor", "Lexbor", "https://github.com/lexbor/lexbor",
         "lexbor/lexbor", "2.3.x", "active 2024-2025", "~100k LOC C",
         "static lib", "Apache-2.0", "none", "low", "low",
         "cmake simple", "small", "parser slot only",
         "spec-compliant HTML5 parser (tokenization/tree)",
         "HTML parse conformance tier", "WebView APKs",
         "VERY ACTIVE", "GOOD", "EVALUATE",
         "If litehtml's parser subset is insufficient, lexbor provides the WHATWG parse law; layout stays litehtml/own thin CSS layer.",
         "EVALUATE", ["MC-095"], "M-16"),
    cand("miniz", "miniz", "https://github.com/richgel999/miniz",
         "richgel999/miniz", "3.0.2", "maintained", "~6k LOC (3 files)",
         "static lib", "MIT", "none", "negligible", "negligible", "trivial",
         "tiny", "same APK-container slot", "ZIP/DEFLATE in one drop",
         "APK container fallback", "all APKs", "ACTIVE", "GOOD",
         "EVALUATE",
         "Alternative to zlib only if static-link/no-system-lib constraints appear; zlib already lawful.",
         "EVALUATE", ["MC-001"], "docs/development/DO_NOT_REINVENT.md"),
    cand("dr_libs", "dr_libs (dr_wav/dr_mp3/dr_flac)",
         "https://github.com/mackron/dr_libs", "mackron/dr_libs",
         "2024-2025 snapshots", "active", "~10k LOC total (3 headers)",
         "in audio_engine", "CC0/PUBLIC DOMAIN / MIT-0", "none",
         "negligible", "negligible", "header-only", "tiny", "0",
         "WAV/MP3/FLAC decode incl. FLAC depth libsndfile may lack",
         "FLAC decode gap (MC-090)", "lossless-audio APKs", "VERY ACTIVE",
         "GOOD", "EVALUATE",
         "Closes the FLAC decode gap with zero dependencies; adopt when a corpus APK demands FLAC (measure first).",
         "EVALUATE", ["MC-090"], "MC-090 FLAC roots"),
    cand("miniaudio", "miniaudio", "https://github.com/mackron/miniaudio",
         "mackron/miniaudio", "0.19.x", "active 2024-2025",
         "~13k LOC (1 header)", "in audio_engine", "MIT-0",
         "none (backend-abstracts WASAPI/ALSA/pulse)", "low", "low",
         "header-only", "small", "0",
         "audio playback device abstraction + decode (wav/mp3/flac)",
         "audio OUTPUT family (MC-090) — device/playback side",
         "audio APKs/games", "VERY ACTIVE", "GOOD",
         "EVALUATE",
         "Current stack decodes (mpg123/sndfile/minimp3/stb_vorbis) but output device handling is host-minimal; miniaudio is the smallest maintained playback layer if real-time playback evidence is required.",
         "EVALUATE", ["MC-090"], "src/audio/audio_engine.cpp"),
    cand("yoga", "Yoga (flexbox)", "https://github.com/facebook/yoga",
         "facebook/yoga", "3.x", "active 2024-2025", "~40k LOC C++",
         "static lib", "MIT", "none", "low", "low",
         "cmake simple", "adapter exists, differential-tested 10/10 <8px; wiring pending (R3)",
         "FlexboxLayout/ConstraintLayout layout slot",
         "flexbox layout solver (CalculateLayout + gentest fixtures)",
         "flexbox/layout family (MC-039/041)", "modern-layout APKs",
         "VERY ACTIVE", "GOOD", "INTEGRATE",
         "Already measured (10/10 differential); finishing the wiring is reuse of a proven component, not new code.",
         "PLANNED", ["MC-039", "MC-041"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md flexbox row (R3)"),

    # ============ ORACLES / REFERENCE-ONLY ==================================
    cand("jadx", "jadx", "https://github.com/skylot/jadx", "skylot/jadx",
         "1.5.x", "active 2025", "n/a (tool)", "tool binary", "GPL-3.0",
         "java", "n/a", "n/a", "tool download", "0 (oracle only)", "0",
         "DEX->Java decompile, DEX parse",
         "DEX diff oracle (MC-017/018/019)", "corpus census tooling",
         "VERY ACTIVE", "GOOD", "ORACLE",
         "Runtime DEX stays in-repo; jadx is the diff-test oracle (PORT_TEST).",
         "ORACLE", ["MC-017", "MC-018", "MC-019"],
         "docs/GRAPHICS_SOURCE_REGISTRY.md (R6 oracles)"),
    cand("androguard", "androguard", "https://github.com/androguard/androguard",
         "androguard/androguard", "3.3.5/4.x", "maintained", "n/a (tool)",
         "python pkg", "Apache-2.0", "python3", "n/a", "n/a", "pip", "0",
         "0", "APK/ARSC/AXML parse oracle",
         "ARSC/AXML diff oracle (MC-004/010)", "census tooling",
         "ACTIVE", "GOOD", "ORACLE",
         "Same oracle law as jadx for resources.",
         "ORACLE", ["MC-004", "MC-010"], "S94 registry (R6)"),
    cand("apktool_arsclib", "ApkTool / ARSCLib",
         "https://github.com/iBotPeaches/Apktool ; https://github.com/reandroid/ARSCLib",
         "iBotPeaches/Apktool ; reandroid/ARSCLib", "2.10 / 1.3.x",
         "active 2025", "n/a (tools)", "tool binaries",
         "Apache-2.0", "java", "n/a", "n/a", "download", "0", "0",
         "APK repack/ARSC parse oracles",
         "resource diff oracles", "census tooling", "VERY ACTIVE", "GOOD",
         "ORACLE",
         "Keep custom runtime, diff-test against these (S94 R6 law).",
         "ORACLE", ["MC-004", "MC-001"], "S94 registry (R6)"),
    cand("aosp_input", "AOSP frameworks/base input laws",
         "https://android.googlesource.com/platform/frameworks/base",
         "aosp-mirror/platform_frameworks_base", "android-14.0.0_r2",
         "committed docs/upstream/aosp/", "committed snapshot subset",
         "ported into runtime", "Apache-2.0", "none", "low", "low",
         "n/a (source of laws)", "done for the ported set",
         "touch_dispatcher/gesture/scroller/key_event shadow files",
         "ViewGroup.dispatchTouchEvent, TouchTarget, onInterceptTouchEvent, VelocityTracker LSQ2, TouchDelegate, GestureDetector, Scroller/OverScroller, FocusFinder, KeyCharacterMap",
         "the ENTIRE INPUT cluster (MC-051..055) — see docs/REUSE_AUDIT_INPUT.md",
         "whole interactive corpus", "VERY ACTIVE", "THE reference (Android itself)",
         "REFERENCE_ONLY (PORT-LAWS 1:1)",
         "INPUT-cluster reuse verdict: AOSP IS the mature, maintained implementation; laws are ported 1:1 with anchors. No third-party input library can beat this (SDL2/libinput = device layer; robolectric/espresso = test-only). Remaining INPUT work is adapter-level evidence waves, not new subsystems.",
         "REFERENCE_ONLY", ["MC-050", "MC-051", "MC-052", "MC-053", "MC-054", "MC-055", "MC-049"],
         "docs/upstream/aosp/s130_laws/; R-NEW-424/425/426; S130 batch"),
    cand("skia", "Skia", "https://github.com/google/skia", "google/skia",
         "chrome/m142 line", "active 2025", "~2M LOC", "n/a", "BSD-3 + Apache-2.0",
         "many", "medium-high", "medium", "large build", "n/a", "n/a",
         "2D raster, clip stack, AA, text, GPU backends",
         "clip/AA law source (MC-080/064)", "all rendering", "VERY ACTIVE",
         "STABLE", "REFERENCE_ONLY",
         "Porting Skia wholesale would violate smallest-practical-component law; laws (clip MCRec stack, AA coverage) are ported and MEASURED by the verifier instead.",
         "REFERENCE_ONLY", ["MC-080", "MC-064", "MC-065", "MC-066"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md Skia row"),
    cand("cdroid", "cdroid", "https://github.com/houstudio/cdroid",
         "houstudio/cdroid", "current", "maintained (moderate churn)",
         "~100k LOC C++", "n/a", "LGPL-2.1 (sha-pinned)", "none", "low", "low",
         "cmake", "n/a — behavioral reference / dynamic link only",
         "none (reference)", "View/Drawable/NinePatch/Ripple/AnimationDrawable/StaticLayout semantics",
         "view/drawable semantic family (MC-037/068)", "themed APKs",
         "ACTIVE", "MEDIUM", "REFERENCE_ONLY",
         "S94 discovery: primary C++ Android-GUI semantic reference; LGPL means behavioral reference or dynamic link, never static copy without compliance.",
         "REFERENCE_ONLY", ["MC-037", "MC-068"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md cdroid row"),
    cand("aosp_compose", "AndroidX Compose / skiko",
         "https://android.googlesource.com/platform/frameworks/support ; https://github.com/JetBrains/skiko",
         "androidx ; JetBrains/skiko", "current", "active 2025",
         "n/a", "n/a", "Apache-2.0", "kotlin", "n/a", "n/a", "n/a", "n/a",
         "n/a", "LayoutNode recomposition laws, SkiaLayer redraw laws",
         "Compose family (MC-099) — R-NEW-344 recomposer", "21 Compose titles",
         "VERY ACTIVE", "GOOD", "REFERENCE_ONLY",
         "Compose is ported as LAWS (R-NEW-344 already VERIFIED-FIXED); wholesale Compose integration is out of smallest-component scope until measured need.",
         "REFERENCE_ONLY", ["MC-099", "MC-100"],
         "M-06; R-NEW-344"),
    cand("godot_libgdx", "Godot / libGDX loop laws",
         "https://github.com/godotengine/godot ; https://github.com/libgdx/libgdx",
         "godotengine/godot ; libgdx/libgdx", "current", "active",
         "n/a", "n/a", "MIT ; Apache-2.0", "n/a", "n/a", "n/a", "n/a",
         "n/a", "n/a", "fixed-step Main::iteration timing; AndroidGraphics.onDrawFrame surface submission",
         "game-loop timing oracle (MC-115) + ANIMATION_FROZEN discrimination",
         "game corpus (91 titles)", "VERY ACTIVE", "GOOD",
         "REFERENCE_ONLY",
         "Timing oracles only — the runtime keeps its own deterministic virtual-clock loop.",
         "REFERENCE_ONLY", ["MC-115", "MC-089"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md surface/loop rows"),
    cand("pixelmatch", "pixelmatch", "https://github.com/mapbox/pixelmatch",
         "mapbox/pixelmatch", "5.x", "maintained", "~500 LOC", "n/a",
         "ISC", "none", "n/a", "n/a", "port to verifier", "small (port)",
         "verifier diff function", "AA-aware pixel diff (colorDelta, antialiasing)",
         "verifier WRONG_COLOR false-positive class (MC-122/123)",
         "all evidence", "STABLE", "GOOD", "PORT_TEST",
         "Adopted-by-port when measured false positives require AA detection; already cross-checked with dHash/color-hash.",
         "PLANNED", ["MC-122", "MC-123"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md visual diff row"),
    cand("tesseract", "tesseract", "https://github.com/tesseract-ocr/tesseract",
         "tesseract-ocr/tesseract", "5.x", "active", "~150k LOC", "tool/lib",
         "Apache-2.0", "leptonica", "medium", "medium", "system package",
         "verifier-side only", "0", "OCR oracle for text evidence",
         "UNREADABLE_TEXT verification (S93 heuristic -> OCR cross-check)",
         "text-bearing APK evidence", "ACTIVE", "GOOD", "PORT_TEST",
         "Turns the UNREADABLE_TEXT law from heuristic into OCR-proven evidence.",
         "PLANNED", ["MC-044", "MC-077"],
         "docs/GRAPHICS_DO_NOT_REINVENT.md OCR row"),
    cand("sdl2", "SDL2", "https://github.com/libsdl-org/SDL", "libsdl-org/SDL",
         "2.30.x", "active 2025", "~200k LOC", "n/a", "zlib", "many host",
         "low", "low", "system package", "n/a", "n/a",
         "window/input/audio device abstraction",
         "REJECTED for runtime (headless virtual-clock driver is the evidence law); potential host-UI viewer only",
         "n/a", "VERY ACTIVE", "GOOD", "REJECTED",
         "The runtime is headless with deterministic virtual-clock input; SDL solves a problem (real-time device I/O) the evidence pipeline deliberately does not have. Revisit only for an interactive host viewer.",
         "REJECTED", ["MC-051", "MC-090"],
         "this audit"),
    cand("curl", "libcurl", "https://curl.se", "curl/curl", "8.x",
         "active 2025", "~200k LOC", "linked -lcurl", "curl license (MIT-like)",
         "openssl/nghttp2", "low", "low", "system package", "small",
         "http_client substrate swap", "HTTP/1.1/2, POST, keep-alive, pooling, proxies, cookies",
         "HTTP depth family (MC-109/110)", "networked APKs",
         "VERY ACTIVE", "STABLE", "EVALUATE",
         "Trigger recorded: adopt curl when corpus demands POST/keep-alive/HTTP2 — the current GET-law client (libcore semantics over OpenSSL) covers measured need; upgrade substrate instead of writing more client code.",
         "EVALUATE", ["MC-109", "MC-110"], "S100 NET-001 scope note"),
    cand("rlottie_upstream", "Samsung rlottie",
         "https://github.com/Samsung/rlottie", "Samsung/rlottie", "0.2.x",
         "LOW CHURN (frozen-ish)", "~80k LOC C++", "static lib",
         "MIT", "none", "low", "low", "cmake", "small", "replace RLottieDecoder core",
         "Lottie vector animation rendering",
         "Lottie family (Telegram tgs/animations)", "Telegram animations",
         "STABLE (upstream slowed)", "MEDIUM", "EVALUATE",
         "Honesty note: current RLottieDecoder is a custom Lottie-JSON renderer (format-level), NOT the upstream library (S94 table overstated 'integrated'). If Lottie fidelity gaps are measured, swap the core for upstream rlottie rather than extending the custom renderer.",
         "EVALUATE", ["MC-088"], "src/renderer/software_renderer.h RLottieDecoder; S94 correction"),
]

# Category -> candidate ids (enrichment law §8: extend master_worklist.json)
CAT2CAND = {
    "MC-001": ["zlib", "miniz"],
    "MC-004": ["androguard", "apktool_arsclib"],
    "MC-008": ["nanosvg", "resvg"],
    "MC-010": ["androguard"],
    "MC-017": ["jadx"], "MC-018": ["jadx"], "MC-019": ["jadx"],
    "MC-037": ["cdroid"], "MC-039": ["yoga"], "MC-041": ["yoga"],
    "MC-044": ["tesseract"], "MC-049": ["aosp_input"],
    "MC-050": ["aosp_input"], "MC-051": ["aosp_input", "sdl2"],
    "MC-052": ["aosp_input"], "MC-053": ["aosp_input"],
    "MC-054": ["aosp_input"], "MC-055": ["aosp_input"],
    "MC-064": ["skia", "libpng", "libjpeg-turbo", "libwebp", "stb_image"],
    "MC-065": ["skia"], "MC-066": ["skia"],
    "MC-067": ["libpng", "libjpeg-turbo", "libwebp", "stb_image"],
    "MC-068": ["cdroid"],
    "MC-074": ["freetype"], "MC-075": ["freetype"],
    "MC-076": ["harfbuzz"], "MC-077": ["harfbuzz", "fribidi"],
    "MC-078": ["harfbuzz"],
    "MC-080": ["skia", "portablegl"], "MC-088": ["rlottie_upstream"],
    "MC-089": ["gif_s106", "stb_image", "wuffs", "libnsgif"],
    "MC-090": ["mpg123", "libsndfile", "minimp3", "stb_vorbis", "dr_libs",
               "miniaudio"],
    "MC-091": ["ffmpeg"],
    "MC-094": ["quickjs", "litehtml", "lexbor"],
    "MC-095": ["litehtml", "lexbor"],
    "MC-097": ["quickjs"], "MC-098": ["litehtml", "quickjs"],
    "MC-099": ["aosp_compose"], "MC-100": ["aosp_compose"],
    "MC-104": ["sqlite3"], "MC-105": ["sqlite3"],
    "MC-109": ["openssl", "http_client", "curl"],
    "MC-110": ["openssl", "http_client", "curl"],
    "MC-114": ["portablegl", "skia"],
    "MC-115": ["godot_libgdx"], "MC-116": ["aosp_input"],
    "MC-122": ["pixelmatch"], "MC-123": ["pixelmatch"],
    "MC-128": ["openssl"],
}


def main():
    os.makedirs(CANON, exist_ok=True)
    # 1. registry
    by_id = {c["REUSE_CANDIDATE"]: c for c in CANDIDATES}
    assert len(by_id) == len(CANDIDATES), "duplicate REUSE_CANDIDATE ids"
    counts = {}
    for c in CANDIDATES:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    reg = {
        "schema": "reuse_registry/1 (S131 REUSE-FIRST GLOBAL LAW)",
        "law": ("For every unresolved capability: search existing MiniAndroid "
                "implementation, AOSP, AndroidX, libcore/ART, mature open-source, "
                "embeddable libraries, maintained projects, compatibility "
                "projects — ONLY THEN design new. Generated; edit this script, "
                "not the JSON."),
        "mandated_fields": ["REUSE_CANDIDATE", "SOURCE_URL", "UPSTREAM_PROJECT",
                            "VERSION", "LAST_UPDATE", "SOURCE_SIZE",
                            "BINARY_SIZE_IF_RELEVANT", "LICENSE", "DEPENDENCIES",
                            "CPU", "RAM", "BUILD_COST", "INTEGRATION_COST",
                            "ADAPTER_SIZE", "CAPABILITIES", "ROOTS_ELIMINATED",
                            "APK_COVERAGE", "MAINTENANCE_STATUS", "UPDATEABILITY",
                            "DECISION", "REASON"],
        "honesty": ("VERSION/LAST_UPDATE recorded from upstream docs at S131; "
                    "re-verify at integration time (law §12: research is "
                    "UNVERIFIED until MiniAndroid runtime tests prove it)."),
        "counts": counts,
        "candidates": CANDIDATES,
    }
    with open(f"{CANON}/reuse_registry.json", "w") as f:
        json.dump(reg, f, indent=1)
    print(f"canonical/reuse_registry.json: {len(CANDIDATES)} candidates {counts}")

    # 2. enrich master_worklist.json (idempotent post-generation enrichment)
    wpath = f"{CANON}/master_worklist.json"
    with open(wpath) as f:
        wl = json.load(f)
    enriched = 0
    for it in wl["items"]:
        ids = CAT2CAND.get(str(it["category"]).split()[0], [])
        if ids:
            it["reuse_candidate"] = ids
            enriched += 1
    wl["reuse_map"] = {k: v for k, v in sorted(CAT2CAND.items())}
    wl["reuse_law"] = ("REUSE-FIRST (S131): every item lists its reuse_candidate "
                       "ids; no new subsystem may be hand-written before the "
                       "candidate decision is executed (integrate-or-justify).")
    with open(wpath, "w") as f:
        json.dump(wl, f, indent=1)
    print(f"master_worklist.json: {enriched} items enriched with reuse_candidate")

    # 3. REUSE / EXTERNAL COMPONENT MAP doc
    L = []
    L.append("# REUSE / EXTERNAL COMPONENT MAP (S131 REUSE-FIRST LAW)")
    L.append("")
    L.append("> GENERATED by `scripts/s131_reuse_first.py` — do not hand-edit.")
    L.append("> LAW: MAXIMUM REAL-APK COMPATIBILITY WITH MINIMUM NEW CODE. Before")
    L.append("> ANY new subsystem code: search existing implementation, AOSP,")
    L.append("> AndroidX, libcore/ART, mature open-source, embeddable libraries.")
    L.append("> Machine twin: `canonical/reuse_registry.json` (21 mandated fields")
    L.append("> per candidate). `docs/MASTER_WORKLIST.md` §12 mirrors this map.")
    L.append("")
    L.append("| # | CANDIDATE | STATUS | LICENSE | SOURCE SIZE | CAPABILITIES |")
    L.append("|---|---|---|---|---|---|")
    for i, c in enumerate(CANDIDATES, 1):
        L.append(f"| {i} | **{c['REUSE_CANDIDATE']}** ({c['name']}) | "
                 f"[{c['status']}] | {c['LICENSE']} | {c['SOURCE_SIZE']} | "
                 f"{c['CAPABILITIES'][:110]} |")
    L.append("")
    L.append("## By category (category → candidates)")
    L.append("")
    L.append("| CATEGORY | CANDIDATES |")
    L.append("|---|---|")
    for k in sorted(CAT2CAND):
        L.append(f"| {k} | {', '.join(CAT2CAND[k])} |")
    L.append("")
    L.append("## Decision table")
    L.append("")
    L.append("| CANDIDATE | DECISION | REASON |")
    L.append("|---|---|---|")
    for c in CANDIDATES:
        r = c["REASON"].replace("|", "/")
        L.append(f"| {c['REUSE_CANDIDATE']} | {c['DECISION']} | {r} |")
    L.append("")
    with open(f"{DOCS}/REUSE_EXTERNAL_COMPONENT_MAP.md", "w") as f:
        f.write("\n".join(L))
    print(f"docs/REUSE_EXTERNAL_COMPONENT_MAP.md: {len(L)} lines")

    # 4. INPUT-cluster reuse audit (law §14: run BEFORE more input code)
    L = []
    L.append("# INPUT CLUSTER — REUSE-FIRST AUDIT (S131)")
    L.append("")
    L.append("> GENERATED by `scripts/s131_reuse_first.py`. Law §14 order: audit the")
    L.append("> whole INPUT cluster, search AOSP, search mature implementations, search")
    L.append("> Android-compatibility projects, THEN decide. VERDICT below was computed")
    L.append("> against `canonical/master_worklist.json` (17 INPUT items) and the")
    L.append("> committed AOSP snapshot (docs/upstream/aosp/, android-14.0.0_r2).")
    L.append("")
    L.append("## Verdict")
    L.append("")
    L.append("**AOSP frameworks/base IS the mature, maintained implementation of the")
    L.append("Android input pipeline** — and its laws are already ported 1:1 into the")
    L.append("runtime (S128/S129/S130 waves, each with AOSP line anchors):")
    L.append("")
    L.append("| AOSP LAW (source) | MINIANDROID PORT | ROOT |")
    L.append("|---|---|---|")
    L.append("| ViewGroup.dispatchTouchEvent (child iteration, reverse draw order) | touch_dispatcher.cpp walk | R-NEW-424 |")
    L.append("| TouchTarget chain capture (mFirstTouchTarget per gesture) | touch_dispatcher chain | R-NEW-424 |")
    L.append("| onInterceptTouchEvent (DOWN intercept + mid-gesture CANCEL) | dalvik dispatch_intercept bridge | R-NEW-424 |")
    L.append("| VelocityTracker LSQ2 (HORIZON 100ms, HISTORY 20, 40ms stop reset) | velocity_tracker.{h,cpp} 1:1 | R-NEW-425 |")
    L.append("| TouchDelegate (ctor slopBounds, DOWN exact, MOVE/UP gated, CANCEL clears) | TouchDelegateShadow + dispatcher consult | R-NEW-426 |")
    L.append("| MOVE delivery to target (dispatchTransformedTouchEvent) | dispatcher MOVE arm (action=2) | R-NEW-425 fan-out |")
    L.append("| Scroller/OverScroller (spline fling, viscousFluid, DECELERATION_RATE) | scroller_shadow.{h,cpp} 1:1 | R-NEW-427 |")
    L.append("| GestureDetector (100/500/300/40ms timeouts, LSQ2 velocity) | gesture_detector_shadow.{h,cpp} | R-NEW-429 |")
    L.append("| KeyEvent constants + KeyCharacterMap | key_event_shadow.{h,cpp} | R-NEW-431 |")
    L.append("| FocusFinder beam search | KeyEventModel::focus_search | R-NEW-432 |")
    L.append("| View.scrollTo/onScrollChanged, setChecked, setFocusable, listeners | android_shadows View laws | R-NEW-428/430/433/434 |")
    L.append("")
    L.append("**External-candidate search results (law §7 — compatibility projects):**")
    L.append("")
    L.append("| CANDIDATE | WHAT IT SOLVES | WHY NOT THE INPUT ANSWER |")
    L.append("|---|---|---|")
    L.append("| SDL2 / libinput / evdev | device-level event reading | our runtime is headless with a deterministic virtual-clock driver; device I/O is out of scope by evidence law (see reuse registry `sdl2` REJECTED) |")
    L.append("| Robolectric | JVM test shadow of View | test framework, not a runtime; its shadows mirror the SAME AOSP laws we port directly |")
    L.append("| Espresso / UIAutomator | on-device test drivers | test-only; nothing to integrate for runtime dispatch |")
    L.append("| cdroid | C++ Android-like GUI | LGPL behavioral reference for view semantics — NOT event-dispatch infrastructure (recorded REFERENCE_ONLY) |")
    L.append("")
    L.append("**Conclusion: NO additional input library exists that beats the AOSP")
    L.append("laws we already port. Every remaining INPUT item is adapter-level")
    L.append("integration or evidence, enumerated below. New handwritten input")
    L.append("subsystems are FORBIDDEN; new work = AOSP-law ports + integration waves.")
    L.append("This audit gates any future INPUT implementation (cite it before coding).")
    L.append("")
    L.append("## Per-item audit (all 17 INPUT items)")
    L.append("")
    L.append("| ITEM | STATUS | REUSE MAPPING | REMAINING WORK |")
    L.append("|---|---|---|---|")
    AUDIT = [
        ("R-NEW-191", "PARTIAL", "AOSP MotionEvent coordinate transform (Matrix law)", "coordinate matrix law port (on-demand)"),
        ("R-NEW-251", "PARTIAL", "AOSP hit-test law (isTransformedTouchPointInView)", "hit-test law — CLOSED by R-NEW-424 walk; verify + close"),
        ("R-NEW-252", "PARTIAL", "ordering matrix = S128 reverse draw-order law", "regression-watch; close with evidence"),
        ("R-NEW-253", "PARTIAL", "AOSP pressed-state law (drawableHotspot/setPressed)", "pressed law port (on-demand)"),
        ("R-NEW-356", "VERIFIED", "platform clickable-default style law", "regression watch"),
        ("CAP-INPUT-097", "VERIFIED", "MotionEvent materialization (virtual clock)", "regression watch"),
        ("CAP-INPUT-098", "IMPLEMENTED", "KeyEventShadow (S130) — registry wiring pending", "register shadow + real-APK evidence wave"),
        ("CAP-INPUT-099", "IMPLEMENTED", "dispatcher dispatchTouchEvent", "real-APK fan-out evidence for TESTED tier"),
        ("CAP-INPUT-100", "IMPLEMENTED", "intercept bridge (R-NEW-424)", "real-APK fan-out evidence (sudoku/opencalculator wave, M-01)"),
        ("CAP-INPUT-101", "TESTED", "onTouchEvent consult", "3-run reproducibility for VERIFIED"),
        ("CAP-INPUT-102", "TESTED", "TouchTarget chain (R-NEW-424)", "3-run reproducibility for VERIFIED"),
        ("CAP-INPUT-104", "IMPLEMENTED", "keyboard shadow", "runtime evidence (TESTED tier)"),
        ("CAP-INPUT-105", "VERIFIED", "click law", "regression watch"),
        ("CAP-INPUT-106", "IMPLEMENTED", "long-click (GD 500ms law)", "runtime evidence (TESTED tier)"),
        ("CAP-INPUT-108", "IMPLEMENTED", "VelocityTracker LSQ2 (R-NEW-425)", "real-APK fan-out (drag corpus class)"),
        ("CAP-INPUT-109", "IMPLEMENTED", "GestureDetector (R-NEW-429)", "real-APK fan-out (fling/scroll wave)"),
        ("CAP-INPUT-110", "IMPLEMENTED", "TouchDelegate (R-NEW-426)", "real-APK fan-out"),
    ]
    for i, s, m, rw in AUDIT:
        L.append(f"| {i} | {s} | {m} | {rw} |")
    L.append("")
    L.append("## Next-wave queue (evidence-first, zero new subsystems)")
    L.append("")
    L.append("1. KeyEventShadow registry wiring (S130 leftover; model is law-tested).")
    L.append("2. Real-APK INPUT evidence wave: sudoku + opencalculator intercept (M-01),")
    L.append("   drag corpus (VelocityTracker/GestureDetector), TouchDelegate titles.")
    L.append("3. Close R-NEW-251/252 as superseded-by-R-NEW-424 evidence once the wave passes.")
    L.append("4. On-demand small laws: R-NEW-191 coordinate matrix, R-NEW-253 pressed state")
    L.append("   (both AOSP-anchored; only when a measured APK case demands them).")
    L.append("")
    with open(f"{DOCS}/REUSE_AUDIT_INPUT.md", "w") as f:
        f.write("\n".join(L))
    print(f"docs/REUSE_AUDIT_INPUT.md: {len(L)} lines")


if __name__ == "__main__":
    main()
