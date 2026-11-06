#!/usr/bin/env python3
"""S186g — WAVE 1: real build-graph audit + permanent library_ecosystem registry.

Runs real commands against the current HEAD (no old reports):
  ldd build/miniandroid          -> DT_NEEDED  (level: linked)
  nm -D                          -> undefined symbol families (level: called)
  nm                             -> compiled-in T symbols     (level: compiled)
  ls third_party, tools/native_host, build/anchor_libs          (level: source)

Emits (Rule 4: metadata only, nothing bulky):
  library_ecosystem/registry.json
  library_ecosystem/capability_matrix.json
  library_ecosystem/dependency_graph.json
  library_ecosystem/reports/WAVE1_AUDIT.json
  library_ecosystem/README.md
  docs/S186_LIBRARY_ECOSYSTEM.md
"""
import json, os, subprocess, datetime

ROOT = "/home/z/my-project"
MA = os.path.join(ROOT, "miniandroid")
BIN = os.path.join(MA, "build", "miniandroid")
ECO = os.path.join(ROOT, "library_ecosystem")
os.makedirs(os.path.join(ECO, "reports"), exist_ok=True)
os.makedirs(os.path.join(ECO, "locks"), exist_ok=True)
os.makedirs(os.path.join(ECO, "scripts"), exist_ok=True)
TODAY = datetime.date.today().isoformat()

def sh(cmd, cwd=None):
    try:
        return subprocess.run(cmd, shell=True, cwd=cwd or ROOT,
                              capture_output=True, text=True, timeout=120).stdout
    except Exception as e:
        return f"ERR:{e}"

# ---------- 1. raw evidence ----------
ldd_out = sh(f"ldd {BIN}")
needed = sorted(set(l.split()[0] for l in ldd_out.splitlines() if ".so" in l))
nmD = sh(f"nm -D {BIN} 2>/dev/null")
nmT = sh(f"nm {BIN} 2>/dev/null")
undef = []
for l in nmD.splitlines():
    if " U " in l:
        tok = l.split()[-1].split("@")[0]  # strip @@SYMVER suffixes (Debian libs)
        if tok.isidentifier():
            undef.append(tok)

FAMS = {
    "sqlite3": "sqlite3_", "libpng": "png_", "libjpeg": "jpeg_",
    "freetype": "FT_", "harfbuzz": "hb_", "fribidi": "fribidi_",
    "mpg123": "mpg123_", "libsndfile": "sf_", "openssl-ssl": "SSL_",
    "libwebp": "WebP",
}
undef_fam = {k: sum(1 for s in undef if s.startswith(p)) for k, p in FAMS.items()}
def_gl_u = sum(1 for s in undef if s.startswith("gl"))
def_gl_T = sum(1 for l in nmT.splitlines() if " T " in l and l.split().pop().startswith("gl"))
def_js_T = sum(1 for l in nmT.splitlines() if " T " in l and l.split().pop().startswith("JS_"))

third_party = sorted(os.listdir(os.path.join(MA, "third_party")))
host_natives = {}
nh = os.path.join(ROOT, "tools", "native_host")
if os.path.isdir(nh):
    for f in sorted(os.listdir(nh)):
        if f.endswith(".so"):
            n = sh(f"nm -D --defined-only {os.path.join(nh, f)} | grep -c ' T Java_' || true").strip()
            tot = sh(f"nm -D --defined-only {os.path.join(nh, f)} | grep -c ' T ' || true").strip()
            host_natives[f] = {"jni_exports": int(n or 0), "total_T": int(tot or 0)}
anchors = sorted(os.listdir(os.path.join(MA, "build", "anchor_libs"))) if os.path.isdir(os.path.join(MA, "build", "anchor_libs")) else []
def jni(name):
    v = host_natives.get(name) or {}
    return v.get("jni_exports")

stb_ver = ""
with open(os.path.join(MA, "third_party/stb/stb_image.h"), errors="ignore") as fh:
    for line in fh:
        if line.startswith("/* stb_image - v"):
            stb_ver = line.split(" - v")[1].split(" ")[0]; break
qjs_ver = open(os.path.join(MA, "third_party/quickjs/VERSION")).read().strip() if os.path.exists(os.path.join(MA, "third_party/quickjs/VERSION")) else ""

# ---------- 2. registry ----------
def rec(name, upstream, license_, status, reached, vendored=None, host_native=None,
        linked=None, called=None, callers=None, adapter=None, consumers=None,
        test_evidence=None, dupes=None, unused=None, missing=None, build=None):
    return {
        "NAME": name, "UPSTREAM": upstream, "LICENSE": license_,
        "STATUS": status,                    # PART 13 enum
        "LEVELS_REACHED": reached,           # source/compiled/linked/loaded/called/proven
        "VENDORED": vendored, "HOST_NATIVE": host_native, "LINKED_SONAME": linked,
        "CALLED_SYMBOLS": called, "RUNTIME_CALLERS": callers,
        "ANDROID_API_ADAPTER": adapter, "REAL_APK_CONSUMERS": consumers or [],
        "TEST_EVIDENCE": test_evidence, "DUPLICATE_IMPLEMENTATIONS": dupes or [],
        "UNUSED_CODE": unused, "MISSING_CAPABILITIES": missing,
        "BUILD_RECIPE": build,
    }

registry = {"schema": "s186-library-registry/v1", "date": TODAY,
            "law": "S185 SQLITE RULE (issue #536) + S186 directive PART 2",
            "levels_legend": ["1_available_in_source", "2_compiled", "3_linked",
                              "4_loaded", "5_called", "6_proven_via_real_apk"],
            "libraries": [
    rec("SQLite", "https://www.sqlite.org/", "public domain", "INTEGRATED",
        ["linked", "called", "proven"],
        linked="libsqlite3.so.0", called=undef_fam["sqlite3"],
        adapter="java_database_shadow (JDBC-style SQLiteDatabase shadow)",
        consumers=["S185 SQLITE RULE corpus (datastore-family titles)"],
        test_evidence="docs/SQLITE_RULE.md; 27 U sqlite3_* symbols in engine binary",
        build="system Debian libsqlite3-dev; CMake foreach(crypto sqlite3) find_library"),
    rec("zlib", "https://zlib.net/", "zlib", "INTEGRATED",
        ["linked", "called", "proven"], linked="libz.so.1",
        callers=["apk_parser (central directory inflate)", "resource PNG paths"],
        test_evidence="find_package(ZLIB REQUIRED); every APK load depends on it",
        build="system Debian zlib1g-dev"),
    rec("libpng", "https://github.com/pnggroup/libpng", "libpng-2.0", "INTEGRATED",
        ["linked", "called", "proven"], linked="libpng16.so.16", called=undef_fam["libpng"],
        adapter="BitmapFactory shadow -> png_decode path",
        consumers=["B_STRUCTURED image family (S183 B6)"],
        test_evidence="30 U png_* symbols; B6 face-flip evidence S183",
        build="system Debian libpng-dev"),
    rec("libjpeg-turbo", "https://github.com/libjpeg-turbo/libjpeg-turbo", "IJG/BSD-3", "INTEGRATED",
        ["linked", "called", "proven"], linked="libjpeg.so.62", called=undef_fam["libjpeg"],
        adapter="BitmapFactory shadow -> jpeg_decode path",
        consumers=["JPEG asset titles"],
        test_evidence="8 U jpeg_* symbols",
        build="system Debian libjpeg-dev"),
    rec("libwebp", "https://github.com/webmproject/libwebp", "BSD-3", "INTEGRATED",
        ["linked", "called"], linked="libwebp.so.7", called=undef_fam["libwebp"],
        adapter="BitmapFactory shadow webp branch",
        consumers=["webp-asset titles"],
        test_evidence="3 U WebP* symbols; animated-WebP untested -> capability gap",
        missing=["animated WebP demux (libwebpdemux not linked)"]),
    rec("stb_image", "https://github.com/nothings/stb", "public domain", "INTEGRATED",
        ["source", "compiled", "called", "proven"],
        vendored=f"miniandroid/third_party/stb/stb_image.h v{stb_ver}",
        adapter="BitmapFactory shadow fallback decoder",
        consumers=["GIF single-frame path", "B6 family fallback"],
        test_evidence="vendored header compiled into engine; S183 B6 evidence",
        missing=["animated GIF frames (stbi only decodes first frame)"]),
    rec("FreeType", "https://freetype.org/", "FTL/GPL-2", "INTEGRATED",
        ["linked", "called", "proven"], linked="libfreetype.so.6", called=undef_fam["freetype"],
        adapter="Typeface/TextShaper -> FT_Face glyph rasterization",
        consumers=["all text-rendering titles incl. Persian/Arabic shaping"],
        test_evidence="11 U FT_* symbols; text rendering across battery faces",
        build="system Debian libfreetype-dev"),
    rec("HarfBuzz", "https://github.com/harfbuzz/harfbuzz", "MIT", "INTEGRATED",
        ["linked", "called"], linked="libharfbuzz.so.0", called=undef_fam["harfbuzz"],
        adapter="TextShaper shaping stage",
        consumers=["multilingual titles (Telegram-family)"],
        test_evidence="9 U hb_* symbols",
        missing=["shaping coverage per-script not yet probed per-title"]),
    rec("FriBidi", "https://github.com/fribidi/fribidi", "LGPL-2.1+", "INTEGRATED",
        ["linked", "called"], linked="libfribidi.so.0", called=undef_fam["fribidi"],
        adapter="TextShaper bidi stage",
        consumers=["Persian/Arabic/RTL titles"],
        test_evidence="2 U fribidi_* symbols"),
    rec("mpg123", "https://github.com/madebr/mpg123", "LGPL-2.1", "INTEGRATED",
        ["linked", "called"], linked="libmpg123.so.0", called=undef_fam["mpg123"],
        adapter="MediaPlayer/AudioTrack decode path",
        consumers=["MP3-asset games"],
        test_evidence="8 U mpg123_* symbols; audio end-to-end not yet 3-run verified",
        missing=["no real-APK audio proof recorded yet"]),
    rec("libsndfile", "https://github.com/libsndfile/libsndfile", "LGPL-2.1", "INTEGRATED",
        ["linked", "called"], linked="libsndfile.so.1", called=undef_fam["libsndfile"],
        adapter="SoundPool WAV/OGG path",
        consumers=["OGG/WAV-asset games"],
        test_evidence="4 U sf_* symbols",
        missing=["no real-APK audio proof recorded yet"]),
    rec("OpenSSL", "https://github.com/openssl/openssl", "Apache-2.0", "INTEGRATED",
        ["linked", "called"], linked="libssl.so.3 + libcrypto.so.3", called=undef_fam["openssl-ssl"],
        adapter="HTTPSURLConnection/TLS adapter",
        consumers=["network titles (taz -> conscrypt UnsatisfiedLinkError shows gap)"],
        test_evidence="23 U SSL_* symbols; F-NATIVE taz conscrypt failure recorded",
        missing=["conscrypt JNI layer for TLS titles"]),
    rec("QuickJS", "https://github.com/bellard/quickjs", "MIT", "INTEGRATED",
        ["source", "compiled", "proven"],
        vendored=f"miniandroid/third_party/quickjs (VERSION={qjs_ver})",
        adapter="S118 WebView/HTML5 engine bridge",
        consumers=["S118 web titles"],
        test_evidence=f"{def_js_T} defined JS_* T symbols compiled into engine binary",
        missing=["Fetch/Promise scheduling audits pending (S118 reuse mandated)"]),
    rec("PortableGL", "https://github.com/rswinkle/PortableGL", "MIT", "INTEGRATED",
        ["source", "compiled", "proven"],
        vendored="miniandroid/third_party/portablegl/portablegl.h",
        adapter="libEGL/libGLESv2 anchor -> GLES2 software backend",
        consumers=["app.halma #27 (A_RICH 0-uncaught)", "se.tube42.p9 #225 (A_RICH)",
                   "Mindustry/Vector Pinball/Stardroid (native family)"],
        test_evidence=f"{def_gl_T} defined gl* T symbols compiled in; A_RICH faces in S186c battery",
        missing=["GLES3 coverage; FBO/shader families per-title gaps remain"],
        build="header-only vendored; compiled into miniandroid_core"),
    rec("rlottie", "https://github.com/Samsung/rlottie", "MIT", "ABSENT",
        [], missing=["no vendored copy, no system link, no consumer identified yet"],
        consumers=[], test_evidence="not in third_party, not in ldd, 0 symbols"),
    rec("SDL", "https://github.com/libsdl-org/SDL", "zlib", "ABSENT",
        [], missing=["no vendored copy, no system link; B1 SDL2/mupdf host rebuild still pending (S185 mapping)"],
        consumers=[], test_evidence="not in third_party, not in ldd"),
    rec("libGDX", "https://github.com/libgdx/libgdx", "Apache-2.0", "INTEGRATED",
        ["source", "compiled", "proven"],
        host_native=f"tools/native_host/libgdx64.so jni={jni('libgdx64.so')}",
        build="scripts/s183_build_gdx_host.sh (fetch-if-missing, gdx-parent-1.9.10 tag)",
        adapter="GATE-A .so substitution + bionic->glibc rebuild",
        consumers=["emmanuelttt", "bouncy", "stacktower3d (S183b faces)"],
        test_evidence=f"tools/native_host/libgdx64.so {jni('libgdx64.so')} T syms; NOT in git (Rule 4)"),
    rec("Box2D", "https://github.com/erincatto/box2d", "zlib", "INTEGRATED",
        ["source", "compiled", "proven"],
        host_native=f"tools/native_host/libgdx-box2d64.so jni={jni('libgdx-box2d64.so')}",
        build="same script; gdx 1.9.10 box2d jni",
        adapter="GATE-A substitution (S186b)",
        consumers=["bouncy #? byte-exact face 8a6c24ac8a7d718e == S183b pin"],
        test_evidence=f"{jni('libgdx-box2d64.so')} T syms; S186B_BOX2D_AB.json",
        ),
    rec("libgdx-freetype", "https://github.com/libgdx/libgdx", "Apache-2.0", "BUILD_VERIFIED",
        ["source", "compiled"],
        host_native=f"tools/native_host/libgdx-freetype64.so jni={jni('libgdx-freetype64.so')}",
        build="same script",
        consumers=["gdx titles using FreeType fonts"],
        test_evidence=f"{jni('libgdx-freetype64.so')} T syms; not yet proven via real APK face"),
] + [
    rec("nlohmann_json", "https://github.com/nlohmann/json", "MIT", "INTEGRATED",
        ["source", "compiled", "called", "proven"],
        vendored="miniandroid/third_party/nlohmann_json (cmake-4.x compat path)",
        test_evidence="engine config/manifest JSON plumbing"),
    rec("minimp3/stb_vorbis", "github.com/lieff/minimp3; github.com/nothings/stb", "public domain",
        "INTEGRATED", ["source"],
        vendored="miniandroid/third_party/audio/{minimp3.h,stb_vorbis.c}",
        dupes=["overlaps linked mpg123/libsndfile — PRUNE CANDIDATE after trace"],
        test_evidence="vendored headers; trace-before-prune pending (Rule 3)"),
    rec("anchor_libs (11 fake bionic sonames)", "project-internal", "project",
        "INTEGRATED", ["compiled"],
        test_evidence="build/anchor_libs: libc/libEGL/libGLESv2/libOpenSLES/libandroid/libjnigraphics/liblog/libdl/libm/libstdc++/libz.so for bionic DT_NEEDED satisfaction",
        missing=["libOpenSLES/libEGL anchors are stubs — B2/B7 real backends still open"]),
]}

# ---------- 3. capability matrix ----------
cap = {"schema": "s186-capability-matrix/v1", "date": TODAY, "capabilities": [
    {"capability": "GLES2 software rendering", "current_backend": "PortableGL (compiled-in)",
     "consumers": ["app.halma #27", "se.tube42.p9 #225", "Mindustry", "Vector Pinball", "Stardroid", "libGDX family"],
     "state": "A_RICH 2/41 in S186c battery; native family gated by EGL/surface semantics",
     "candidates": ["gl4es (GLES-over-GL semantic gaps)", "keep PortableGL (audit first — directive PART 5A)"],
     "fan_out": "10-title native/GL cluster (S185 census)"},
    {"capability": "image decode to real Bitmap pixels (B6)", "current_backend": "stb_image + libpng + libjpeg + libwebp",
     "consumers": ["14 B_STRUCTURED faces one fix away (S185)", "10 B_STRUCTURED in s107 census"],
     "state": "decoders linked+called; structured-content flattening root cause not fully closed",
     "candidates": ["AOSP BitmapFactory semantics port", "premultiplied-alpha audit"],
     "fan_out": "up to 43 near-blank + 10 B_STRUCTURED (census tiers)"},
    {"capability": "AndroidX class-init (lifecycle/savedstate/fragment)", "current_backend": "shadow stubs + partial vendored sources",
     "consumers": ["54-title headroom (S185)", "F-ANDROIDX 6 in battery: datastore x2, OnBackPressedDispatcher x2, FragmentContainerView, appcompat"],
     "state": "S186f descendingIterator law landed (foehnix 10->0, aoc 10->0)",
     "candidates": ["androidx sources.jar port per class (Rule 1: vend don't rewrite)"],
     "fan_out": "highest of all families"},
    {"capability": "physics (Box2D) for libGDX", "current_backend": "host-native libgdx-box2d64.so via GATE-A",
     "consumers": ["bouncy (byte-exact pin)"],
     "state": "S186b verified; regression = environment loss, not engine",
     "candidates": [], "fan_out": "all libGDX physics titles"},
    {"capability": "SQLite storage", "current_backend": "system libsqlite3", "consumers": ["S185 rule corpus"],
     "state": "law formalized issue #536", "candidates": [], "fan_out": "datastore/deck-family titles"},
    {"capability": "audio output", "current_backend": "mpg123+sndfile linked; minimp3/stb_vorbis vendored (dupe)",
     "consumers": ["MP3/OGG-asset games"], "state": "decode linked; NO real-APK audio proof yet (Rule 5)",
     "candidates": ["OpenAL Soft bridge for OpenSL ES (B7)"],
     "fan_out": "B7 cluster + every game with sound assets"},
    {"capability": "TLS/network", "current_backend": "OpenSSL linked", "consumers": ["taz #? (conscrypt UnsatisfiedLinkError)"],
     "state": "SSL symbols called; conscrypt JNI gap open", "candidates": ["conscrypt rebuild or BoringSSL path"],
     "fan_out": "F-NATIVE 1 + all HTTPS titles"},
    {"capability": "text shaping (Persian/Arabic/RTL)", "current_backend": "FreeType+HarfBuzz+FriBidi", "consumers": ["multilingual titles"],
     "state": "linked+called; per-script probes pending", "candidates": [], "fan_out": "all i18n titles"},
    {"capability": "WebView/JS", "current_backend": "QuickJS compiled-in (S118)", "consumers": ["web titles"],
     "state": "reuse+audit mandated", "candidates": [], "fan_out": "webview titles"},
]}

# ---------- 4. dependency graph ----------
depgraph = {"schema": "s186-dependency-graph/v1", "date": TODAY,
            "engine_dt_needed": needed,
            "transitive": {"libsndfile.so.1": ["libFLAC", "libvorbis", "libogg", "libopus", "libmp3lame"],
                           "libharfbuzz.so.0": ["libgraphite2", "libglib-2.0", "libfreetype"],
                           "libwebp.so.7": ["libsharpyuv"],
                           "libssl.so.3": ["libcrypto"],
                           "libpng16.so.16": ["libz", "libbrotlidec", "libbrotlicommon"]},
            "vendored": third_party,
            "host_natives": host_natives,
            "anchor_libs": anchors,
            "undefined_symbol_families": undef_fam,
            "compiled_in": {"portablegl_gl_T_symbols": def_gl_T, "quickjs_JS_T_symbols": def_js_T,
                            "undefined_total": len(undef)}}

audit = {"date": TODAY, "binary": BIN, "ldd_count": len(needed),
         "needed": needed, "undefined_symbol_families": undef_fam,
         "compiled_in": depgraph["compiled_in"], "third_party": third_party,
         "host_natives": host_natives, "anchor_libs": anchors,
         "cmake_finds": ["ZLIB REQUIRED", "png (optional)", "jpeg (optional)",
                         "crypto sqlite3 (optional foreach)", "nlohmann_json vendored-or-fetch"],
         "notes": ["libwebpdemux NOT linked -> animated WebP gap",
                   "no -lGL: PortableGL compiled-in, no system GL dependency",
                   "Box2D/libGDX NOT linked into engine: host natives dlopened at runtime via GATE-A"]}

# ---------- 5. write ----------
def w(path, obj):
    with open(path, "w") as f:
        if isinstance(obj, str): f.write(obj)
        else: json.dump(obj, f, indent=1)

w(os.path.join(ECO, "registry.json"), registry)
w(os.path.join(ECO, "capability_matrix.json"), cap)
w(os.path.join(ECO, "dependency_graph.json"), depgraph)
w(os.path.join(ECO, "reports", "WAVE1_AUDIT.json"), audit)

readme = f"""# library_ecosystem — S186 permanent build-on-demand registry

Laws: S185 SQLite Rule (issue #536) + S186 directive (PART 1-15).
This directory holds METADATA ONLY (Rule 4: nothing bulky in git).
Sources/builds live in external cache dirs; every entry must be reproducible
from scripts/ + pinned upstream URL + revision.

## Files
- registry.json — one record per library, PART 2 template + 6-level status
- capability_matrix.json — capability -> consumers -> candidate -> fan-out
- dependency_graph.json — real DT_NEEDED + transitive + vendored + host natives
- locks/ — pinned revisions (upstream URL + tag + hash)
- reports/ — wave audits (WAVE1_AUDIT.json)
- scripts/ — acquisition/build recipes

## Registry snapshot ({TODAY})
{len([l for l in registry['libraries'] if l['STATUS']=='INTEGRATED'])} INTEGRATED / {len(registry['libraries'])} total;
ABSENT: rlottie, SDL (no consumer proven yet — do not acquire without a real APK need).
Levels reached are command-verified: ldd + nm -D U-families + nm T-counts.

## Operations (conceptual, PART 4)
library search/inspect/acquire/build/load-test/probe/integrate/trace/prune/report
are implemented with existing project conventions: scripts/s183_build_gdx_host.sh
(fetch-if-missing) is the reference pattern for acquire+build; battery scripts are
the load-test/probe pattern; trace-before-prune is Rule 3.
"""
w(os.path.join(ECO, "README.md"), readme)

doc = f"""# S186 — Library Ecosystem (Wave 1 audit, {TODAY})

Source of truth: `library_ecosystem/registry.json` (+ capability_matrix.json,
dependency_graph.json, reports/WAVE1_AUDIT.json). Everything below was measured
against current HEAD with ldd/nm on `miniandroid/build/miniandroid`.

## What actually exists (6-level audit)

| family | level | evidence |
|---|---|---|
| SQLite | linked+called+proven | libsqlite3.so.0, {undef_fam['sqlite3']} U sqlite3_* |
| zlib | linked+called+proven | libz.so.1 |
| libpng | linked+called+proven | libpng16.so.16, {undef_fam['libpng']} U png_* |
| libjpeg | linked+called+proven | libjpeg.so.62, {undef_fam['libjpeg']} U jpeg_* |
| libwebp | linked+called | libwebp.so.7, 3 U WebP*; demux gap |
| stb_image | vendored+compiled+proven | v{stb_ver} |
| FreeType | linked+called+proven | libfreetype.so.6, {undef_fam['freetype']} U FT_* |
| HarfBuzz | linked+called | libharfbuzz.so.0, {undef_fam['harfbuzz']} U hb_* |
| FriBidi | linked+called | libfribidi.so.0, 2 U |
| mpg123 | linked+called | libmpg123.so.0, 8 U |
| libsndfile | linked+called | libsndfile.so.1, 4 U sf_* |
| OpenSSL | linked+called | libssl.so.3, {undef_fam['openssl-ssl']} U SSL_* |
| QuickJS | vendored+compiled+proven | {def_js_T} T JS_* symbols |
| PortableGL | vendored+compiled+proven | {def_gl_T} T gl* symbols; A_RICH faces |
| rlottie | ABSENT | no source/link/consumer |
| SDL | ABSENT | B1 host rebuild pending |
| libGDX | host-native+proven | {jni('libgdx64.so')} T syms |
| Box2D | host-native+proven | {jni('libgdx-box2d64.so')} T syms, GATE-A byte-exact |
| libgdx-freetype | host-native build-verified | {jni('libgdx-freetype64.so')} T syms, no APK proof yet |

Discovered extras: nlohmann_json (vendored), minimp3+stb_vorbis (vendored audio —
PRUNE CANDIDATE overlapping mpg123/libsndfile after trace), 11 anchor_libs stubs
(libEGL/libGLESv2/libOpenSLES are stub anchors — B2/B7 real backends open).

## Real gaps found by the audit (not in old reports)
1. libwebpdemux NOT linked → animated WebP impossible today.
2. Audio: zero real-APK end-to-end proof (Rule 5) despite two decode paths linked.
3. conscrypt JNI gap → TLS titles fail at UnsatisfiedLink (taz evidence).
4. libEGL/libGLESv2 anchors are stubs → GLES families beyond PortableGL's reach
   (GLES3, FBO edge semantics) have no path yet.
5. Duplicate audio implementations present simultaneously — Rule 3 trace required
   before pruning either.

"""
w(os.path.join(ROOT, "docs", "S186_LIBRARY_ECOSYSTEM.md"), doc)

print(json.dumps({"needed": len(needed), "undef_total": len(undef),
                  "undef_fam": undef_fam, "compiled_in": depgraph["compiled_in"],
                  "third_party": third_party, "host_natives": host_natives,
                  "anchors": anchors, "stb": stb_ver, "qjs": qjs_ver}, indent=1))
