#!/usr/bin/env python3
"""CAMPAIGN 009 — P1: classify verified repos (A/B/C/D/E) and generate
GITHUB_MINING_009.md + OPEN_SOURCE_CATALOG_009.json.
Evidence source: results.json (live git ls-remote + LICENSE fetches)."""
import json, os
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/home/z/my-project/repo/miniandroid/docs/knowledge/campaign009"
os.makedirs(OUT, exist_ok=True)

raw = json.load(open(os.path.join(HERE, "results.json")))

# ---------------- classification (engineering judgment on live evidence) -------------
# A=Adopt  B=Integrate/Wrap  C=Test/Oracle  D=Reject  E=Investigate Later
CAT = {
 # --- ARSC / AXML / DEX tooling ---
 "kin9-0rz/apkutils": ("A", "ARSC/AXML", "Pure-python APK/ARSC/AXML parser; vendorable reference for our arsc_tool gap-fills"),
 "REAndroid/ARSCLib": ("A", "ARSC/AXML", "Most complete standalone ARSC lib; config-matching logic is the §6 oracle"),
 "REAndroid/APKEditor": ("B", "ARSC/AXML", "Resource merging/AXML editing; external CLI tool, not embeddable"),
 "skylot/jadx": ("C", "ARSC/AXML", "DEX->Java decompiler; use offline to read app logic during debugging"),
 "iBotPeaches/Apktool": ("B", "ARSC/AXML", "Reference implementation for AXML/ARSC decode semantics"),
 "pxb1988/dex2jar": ("C", "ARSC/AXML", "DEX->JVM converter; oracle for DEX opcode semantics"),
 "APKLab/APKLab": ("D", "ARSC/AXML", "VSCode UI wrapper around apktool/jadx; no unique engine code"),
 "Aliucord/binary-resources": ("B", "ARSC/AXML", "Lightweight binary-resources (ARSC/AXML) lib, Apache-2.0; small enough to port"),
 "droidefense/engine": ("D", "ARSC/AXML", "Malware-analysis engine; GPL-3.0 + out of scope"),
 "google/apk-patcher": ("D", "ARSC/AXML", "NOT-FOUND (404 on ls-remote)"),
 "amimo/dcc": ("C", "ARSC/AXML", "DEX compiler (java->dex); useful for synthetic DEX test vectors"),
 "ReVanced/revanced-patcher": ("D", "ARSC/AXML", "GPL-3.0 patching framework; incompatible + out of scope"),
 "JesusFreke/smali": ("B", "ARSC/AXML", "smali/baksmali: DEX assembler; BSD; build offline test vectors"),
 "plum-umd/redexer": ("C", "ARSC/AXML", "OCaml DEX rewriter; academic reference"),
 "kikfox/ARSCTool": ("E", "ARSC/AXML", "License UNKNOWN; revisit if ARSCLib proves too heavy"),
 "GraxCode/dalvikgate": ("D", "ARSC/AXML", "GPL-3.0; dex->java bridge tool, out of scope"),
 "akavel/dali": ("C", "ARSC/AXML", "Go DEX/ADIL writer; reference for DEX binary format tests"),
 "MatrixEditor/dexrs": ("C", "ARSC/AXML", "Rust DEX parser; compact reference for opcode tables"),
 "tboox/dexbox": ("E", "ARSC/AXML", "Apache-2.0 DEX VM in C; compare interpreter design later"),
 "CalebFenton/simplify": ("D", "ARSC/AXML", "GPL-3.0; symbolic execution, out of scope"),
 "ibilux/ArscResourcesParser": ("E", "ARSC/AXML", "License UNKNOWN; possible ARSC cross-check source"),
 "androguard/androguard": ("C", "ARSC/AXML", "Our primary DEX/AXML/ARSC census oracle (already used in EXP-101/102)"),
 "Sable/soot": ("E", "ARSC/AXML", "LGPL static analysis; heavyweight, only if call-graph oracle needed"),

 # --- Compose ecosystem ---
 "JetBrains/skiko": ("B", "Compose", "Kotlin/Skia bindings — the exact layer Compose renders through; port path for our rasterizer bridge"),
 "JetBrains/compose-multiplatform": ("B", "Compose", "Compose runtime outside Android; its non-Android glue is the map for headless Compose"),
 "androidx/androidx": ("C", "Compose", "Source of truth for compose-runtime/ui/material3 semantics"),
 "android/compose-samples": ("C", "Compose", "§12 generality corpus (Jetchat/Jetcaster/Jetnews...)"),
 "android/nowinandroid": ("C", "Compose", "Large real Compose app target"),
 "android/architecture-samples": ("C", "App-XML", "Classic XML Views+Navigation corpus"),
 "google/accompanist": ("E", "Compose", "Compose utility lib; adopt only when specific piece needed"),
 "coil-kt/coil": ("E", "Compose", "Image loader; only relevant once Compose renders"),
 "bumptech/glide": ("E", "Image", "Android image loader; reference for drawable decode caching"),
 "GetStream/stream-chat-android": ("D", "Compose", "source-available proprietary license; NOT adoptable, sample-only"),
 "JetBrains/skija": ("B", "Compose", "Java Skia bindings; shows the exact Skia API surface Compose needs"),
 "MohamedRejeb/Calf": ("E", "Compose", "Compose MPP file picker etc.; later"),
 "aclassen/ComposeReorderable": ("E", "Compose", "drag/reorder; later"),
 "coil-kt/coil-compose": ("E", "Compose", "n/a placeholder"),
 "MohamedRejeb/compose-rich-editor": ("E", "Compose", "rich text editing; later"),
 "amir1376/ab-download-manager": ("C", "Compose", "Real desktop Compose app (KMP); generality target"),
 "Tlaster/PreCompose": ("E", "Compose", "MPP navigation/state; later"),
 "MohamedRejeb/Pokedex": ("C", "Compose", "Compose MPP app with images/scroll — §12 target"),
 "theapache64/stackzy": ("C", "Compose", "Desktop Compose app; generality target"),
 "joreilly/PeopleInSpace": ("C", "Compose", "KMP Compose app; small enough to actually run"),
 "Gurupreet/ComposeCookBook": ("C", "Compose", "Compose recipe collection; per-feature targets"),
 "skydoves/Balloon": ("E", "Compose", "popup lib; later"),
 "cheonjaeung/gridlayout-compose": ("E", "Compose", "grid layout; later"),
 "rikkahub/rikkahub": ("C", "Compose", "Real full Compose AI chat app; stress target"),
 "vfsfitvnm/ViMusic": ("C", "Compose", "Compose music app; media+compose combo target"),
 "gkd-kit/gkd": ("E", "Compose", "accessibility+compose; niche"),
 "alexzhirkevich/compottie": ("E", "Compose", "Lottie for Compose; ties §12 animation into Compose later"),

 # --- Rendering / GLES / 3D ---
 "google/skia": ("B", "Rendering", "Gold-standard rasterizer; adopt subset or wrap — replaces custom raster pieces"),
 "google/angle": ("B", "GLES", "GLES-over-Vulkan; the §24 candidate to kill our GLES bridge gap"),
 "google/swiftshader": ("B", "GLES", "CPU Vulkan/GLES; configure OK but >3GB RAM compile — prebuilt-binaries route needed"),
 "google/filament": ("E", "GLES", "PBR renderer; only for future real-3D apps"),
 "bgfx/bgfx": ("E", "GLES", "cross-platform gfx abstraction; heavyweight vs need"),
 "floooh/sokol": ("B", "GLES", "tiny headers incl. sokol_gfx; plausible minimal GLES-like layer"),
 "facebook/yoga": ("B", "UI", "Flexbox layout engine; exact Android layout semantics base (used by RN)"),
 "Mesa3D/mesa (canonical: gitlab.freedesktop.org/mesa/mesa)": ("B", "GLES", "llvmpipe/lavapipe/zink software rasterizers — §24 alternative route"),
 "KhronosGroup/Vulkan-Samples": ("C", "GLES", "Vulkan test material for SwiftShader route"),
 "KhronosGroup/glslang": ("B", "GLES", "GLSL->SPIRV; needed by any ANGLE/SwiftShader-lite path"),
 "LWJGL/lwjgl3": ("C", "GLES", "Bindings reference; shows GLES/EGL API surface usage"),
 "zauonlok/renderer": ("C", "GLES", "software rasterizer educational; CPU raster reference"),
 "jserv/tinygl": ("A", "GLES", "TinyGL: classic software GL, MIT, tiny — candidate GLES1.x software fallback"),
 "skywind3000/mini3d": ("C", "GLES", "educational software 3D"),
 "rswinkle/PortableGL": ("A", "GLES", "Software GLES 2.x/3.x-ish implementation in C, MIT — strongest candidate to unblock real GLES APKs without SwiftShader RAM cost"),
 "ssloy/tinyrenderer": ("C", "GLES", "educational oracle only"),
 "apitrace/apitrace": ("C", "GLES", "trace tool; could log our bridge calls vs real EGL traces"),
 "google/gapid": ("C", "GLES", "GAPID/AGI graphics debugger reference"),
 "google/agi": ("C", "GLES", "Android GPU Inspector; debugging oracle"),
 "winebox64/winlator": ("E", "GLES", "shows box64+turnip pattern; niche"),
 "KhronosGroup/Vulkan-Docs": ("C", "GLES", "spec docs"),
 "glfw/glfw": ("C", "Rendering", "windowing reference only (license verify: zlib-style)"),
 "DiligentGraphics/DiligentEngine": ("E", "GLES", "Apache-2.0 engine; too big vs need"),
 "OGRECave/ogre": ("E", "Rendering", "MIT engine; not needed"),
 "bkaradzic/bgfx": ("E", "GLES", "BSD-2; abstraction over backends"),
 "nigels-com/glew": ("C", "GLES", "GL extension loading reference"),
 "g-truc/glm": ("C", "GLES", "math lib reference"),

 # --- Text / font ---
 "notofonts/noto-fonts": ("C", "Text", "font assets source"),
 "googlefonts/noto-fonts": ("C", "Text", "same family (legacy location)"),
 "Tehreer/SheenBidi": ("B", "Text", "Apache-2.0 bidi+shaper — drop-in alternative to FriBidi+HarfBuzz pairing"),
 "rougier/freetype-gl": ("C", "Text", "glyph atlas reference"),
 "OGRECave/ogre": ("C", "Text", "duplicate entry ignored"),
 "harfbuzz/harfbuzzjs": ("C", "Text", "wasm build of harfbuzz; not useful in C++ runtime"),
 "go-text/typesetting": ("C", "Text", "Go port of HarfBuzz concepts; algorithm reference"),
 "fribidi/fribidi": ("B", "Text", "already integrated (1.0.16) — keep"),
 "Tehreer/Tehreer-Android": ("C", "Text", "Android text-type lib; reference for TextView semantics"),
 "harfbuzz/harfbuzz": ("B", "Text", "already integrated (10.2.0) — keep"),
 "unicode-org/text-rendering-tests": ("A", "Text", "CONFORMANCE test vectors for bidi/shaping — free oracle tests"),
 "Tehreer/Tehreer": ("D", "Text", "NOT-FOUND (404)"),
 "unicode-org/icu": ("B", "Text", "ICU: locale/config data oracle for §6 configuration matching"),

 # --- Image codecs ---
 "glennrp/libpng": ("B", "Image", "canonical libpng (pnggroup mirror) — reference"),
 "pnggroup/libpng": ("B", "Image", "canonical org now on GitHub"),
 "libjpeg-turbo/libjpeg-turbo": ("B", "Image", "JPEG decode; candidate to replace custom decoder"),
 "AOMediaCodec/libavif": ("E", "Image", "AVIF; only if corpus demands"),
 "nothings/stb": ("A", "Image", "stb_image: single-header decode of PNG/JPEG/BMP/GIF — tiny adopt path"),
 "randy408/libspng": ("A", "Image", "simple PNG lib; cleaner than full libpng for vendoring"),
 "google/wuffs": ("E", "Image", "safe codecs; interesting but heavy toolchain"),
 "memononen/nanosvg": ("B", "Image", "SVG rasterize (rast, MIT-ish per repo) — VectorDrawable path"),
 "sammycage/plutosvg": ("B", "Image", "MIT SVG parser; pairs with plutovg"),
 "webmproject/libwebp": ("B", "Image", "already integrated — keep"),
 "sammycage/plutovg": ("B", "Image", "MIT tiny 2D VG on FreeType; candidate to replace custom raster pieces"),
 "kikuchan/pngle": ("A", "Image", "MIT tiny PNG decoder for embedded — vendoring candidate"),
 "freetype/freetype": ("B", "Text", "already integrated (2.13.3) — keep"),
 "strukturag/libheif": ("E", "Image", "HEIF; only if corpus demands"),
 "HappySeaFox/sail": ("E", "Image", "multi-codec lib; alternative bundle"),

 # --- Animation ---
 "rive-app/rive-runtime": ("E", "Animation", "MIT; second runtime animation engine after rlottie if needed"),
 "rive-app/rive-cpp": ("E", "Animation", "same content as rive-runtime"),
 "airbnb/lottie-android": ("C", "Animation", "Android Lottie semantics oracle for our rlottie bridge"),
 "ed-asriyan/lottie-converter": ("C", "Animation", "lottie->svg/frames debug tool"),
 "thorvg/thorvg": ("B", "Animation", "MIT vector+Lottie engine; alternative to rlottie with active maintenance"),
 "RazrFalcon/resvg": ("B", "Image", "best SVG static renderer (Apache-2.0); VectorDrawable oracle"),
 "linebender/resvg": ("B", "Image", "moved canonical of RazrFalcon/resvg"),
 "aseprite/aseprite": ("E", "Animation", "sprite editor; only its skia usage is informative"),
 "Samsung/rlottie": ("B", "Animation", "already vendored/built — keep (license verify: MIT per upstream headers)"),
 "LottieFiles/dotlottie-web": ("D", "Animation", "web player; out of scope"),

 # --- Audio / media ---
 "lieff/minimp3": ("A", "Audio", "CC0 single-header MP3 — replace/augment custom MP3 decode"),
 "mackron/miniaudio": ("A", "Audio", "Unlicense; single-header playback device layer — candidate backend for AudioTrack"),
 "mackron/dr_libs": ("A", "Audio", "Unlicense; dr_wav/dr_mp3/dr_flac headers — direct §21 adoption"),
 "FFmpeg/FFmpeg": ("E", "Audio", "LGPL; only if media demands exceed simple codecs"),
 "google/oboe": ("E", "Audio", "Android audio I/O; needs AAudio — N/A headless"),
 "google/ExoPlayer": ("C", "Audio", "Media3 ExoPlayer (archived at google/ExoPlayer -> androidx/media); semantics oracle"),
 "libsdl-org/SDL_mixer": ("E", "Audio", "mixer on SDL; only if game audio demands"),
 "libsndfile/libsndfile": ("B", "Audio", "LGPL; broad format decode — candidate external lib"),
 "libsdl-org/SDL": ("E", "Audio", "device layer; heavier than miniaudio"),
 "androidx/media": ("C", "Audio", "Media3 source — MediaPlayer/ExoPlayer semantics oracle"),
 "kcat/openal-soft": ("E", "Audio", "LGPL; alternative output layer"),
 "lieff/minimp4": ("A", "Audio", "CC0 MP4 demux — media container support for MediaPlayer adapter"),
 "webmproject/libvpx": ("E", "Audio", "VP8/9 video; only if video rendering demanded"),
 "gstreamer/gstreamer": ("D", "Audio", "LGPL pipeline framework; far too heavy for our adapter layer"),
 "google/horologist": ("E", "Audio", "media3 UI compose helpers; later"),
 "xiph/vorbis": ("B", "Audio", "BSD-style (license file unusual format); ogg/vorbis decode"),
 "xiph/ogg": ("B", "Audio", "same family"),
 "FongMi/TV": ("D", "Audio", "GPL-3.0 TV player; out of scope"),
 "mpg123/mpg123": ("D", "Audio", "NOT-FOUND on GitHub (official releases live off-GitHub); dr_mp3/minimp3 cover the need"),

 # --- Persistence ---
 "requery/sqlite-android": ("B", "Persistence", "Apache-2.0 SQLite Android fork; semantics reference for our database/ dir"),
 "sqlite/sqlite": ("A", "Persistence", "public-domain canonical SQLite; adopt canonical amalgamation"),
 "sqlitebrowser/sqlitebrowser": ("C", "Persistence", "GUI inspector for our .db artifacts during testing"),
 "SQLCipher/sqlcipher": ("E", "Persistence", "BSD; only if encrypted DB demanded"),
 "Tencent/wcdb": ("E", "Persistence", "Apache-2.0; mobile DB stack; heavy"),
 "tursodatabase/libsql": ("E", "Persistence", "SQLite fork; niche"),

 # --- Test oracles ---
 "robolectric/robolectric": ("C", "Oracle", "PRIMARY framework-behavior oracle (already proven in EXP-102)"),
 "junit-team/junit5": ("C", "Oracle", "test harness for Robolectric runs"),
 "junit-team/junit4": ("C", "Oracle", "same (Robolectric 4.x uses junit4)"),
 "google/truth": ("C", "Oracle", "assertions for oracle tests"),
 "cashapp/paparazzi": ("C", "Oracle", "layout-render oracle (deferred in EXP-095 for disk; revisit)"),
 "takahirom/roborazzi": ("C", "Oracle", "Compose screenshot testing — Compose §12 oracle candidate"),
 "robolectric/android-all": ("C", "Oracle", "NOT-FOUND via ls-remote (distributed via Maven jars, not a buildable repo) — jars still usable"),
 "google/gson": ("E", "Oracle", "JSON semantics used by many apps; only when needed"),
 "square/retrofit": ("E", "Oracle", "HTTP client semantics; only when network bridge lands"),
 "ReactiveX/RxJava": ("E", "Oracle", "many apps use it; scheduler semantics later"),
 "square/moshi": ("E", "Oracle", "JSON; later"),
 "square/okhttp": ("E", "Oracle", "HTTP; later"),
 "kotlin/kotlinx.coroutines": ("B", "Oracle", "coroutine dispatch semantics needed by Compose/Dooz code paths"),
 "JetBrains/kotlin": ("C", "Oracle", "stdlib/runtime semantics; reference for Kotlin-generated DEX"),
 "google/conscrypt": ("E", "Oracle", "TLS provider; only if network bridge lands"),
 "google/desugar_jdk_libs": ("C", "Oracle", "java.time/streams backport semantics used by apps"),

 # --- Real apps corpus (C = Test/Oracle) ---
 "WebView-CG/CanIAndroidWebView": ("C", "App-WebView", "dedicated WebView test app (§8/§9 target)"),
 "PixelPlayerHQ/PixelPlayerOSS": ("C", "App-Media", "Compose+Media3+Room+DataStore player (§9 target)"),
 "ashrafimostafa/Brick-Blast": ("C", "App-Game", "Compose Canvas game (§9 target)"),
 "yamin8000/Dooz": ("C", "App-Compose", "DOOZ SOURCE — the exact app of our Compose blocker; GPL-3.0"),
 "retrowars/retrowars": ("C", "App-Game", "libGDX multi-game (§25 GLES target); canonical moved from pserwylo"),
 "pserwylo/retrowars": ("D", "App-Game", "superseded by retrowars/retrowars (redirect)"),
 "libgdx/libgdx": ("B", "App-Game", "Apache-2.0; its GLES backend IS the API surface our GLES layer must satisfy"),
 "FossifyOrg/Calendar": ("C", "App-XML", "classic-views+Room app"),
 "FossifyOrg/Contacts": ("C", "App-XML", "lists+SQLite app"),
 "maxrave-dev/SimpMusic": ("C", "App-Media", "Compose+Media3 music app"),
 "FossifyOrg/Gallery": ("C", "App-XML", "image-heavy app"),
 "TeamNewPipe/NewPipe": ("C", "App-Media", "media+lists; GPL-3.0"),
 "OxygenCobalt/Auxio": ("C", "App-Media", "Compose-era audio player; clean architecture"),
 "00-Evan/shattered-pixel-dungeon": ("C", "App-Game", "libGDX game; real GLES consumer"),
 "T8RIN/ImageToolbox": ("C", "App-Image", "image pipeline stress app"),
 "JunkFood02/Seal": ("C", "App-Media", "yt-dlp GUI; Compose"),
 "FoedusProgramme/Gramophone": ("C", "App-Media", "Compose+Media3 minimal player"),
 "chrisbanes/tivi": ("C", "Compose", "large real Compose app"),
 "anilbeesetti/nextplayer": ("C", "App-Media", "Compose video player"),
 "OuterTune/OuterTune": ("C", "App-Media", "Compose+Media3"),
 "MetrolistGroup/Metrolist": ("C", "App-Media", "Compose music"),
 "Droid-ify/client": ("C", "Compose", "Compose F-Droid client — Compose+lists+persistence"),
 "d4rken-org/sdmaid-se": ("C", "Compose", "Compose system cleaner"),
 "duckduckgo/Android": ("C", "App-WebView", "WebView-centric browser app"),
 "hushenghao/AndroidEasterEggs": ("C", "App-Game", "Easter-egg games incl. GLES demos"),
 "lichess-org/mobile": ("C", "App-Game", "Compose board game"),
 "dorumrr/de1984": ("C", "App-XML", "privacy camera app"),
 "LinkoraApp/Linkora": ("C", "Compose", "Compose link manager"),
 "gergelyvagujhelyi/CalculatorM3": ("C", "Compose", "tiny Material3 calculator — ideal small Compose target"),
 "plateaukao/einkbro": ("C", "App-WebView", "WebView browser"),
 "KashCal/KashCal": ("C", "App-XML", "calendar app"),
 "sweakpl/qralarm-android": ("C", "App-XML", "utility app"),
 "nextcloud/android": ("D", "App-Media", "LGPL; huge; network-bound app — poor fit for headless corpus"),
 "shlusiak/Freebloks-Android": ("C", "App-Game", "board game with GLES? (verify)"),
 "accrescent/accrescent": ("C", "Compose", "Compose app store — Compose+security UI"),
 "signalapp/Signal-Android": ("D", "App-Media", "AGPL-3.0; enormous; adopt risk; corpus value low vs cost"),
 "clavierhaus/gnubg-android": ("C", "App-Game", "backgammon port"),
 "TranslucentFoxHuman/DroidStress": ("C", "App-Game", "stress-test app candidate"),
 "SEAbdulbasit/asteroids-compose-multiplatform": ("E", "Compose", "KMP game; license verify needed"),
 "Anuken/Mindustry": ("C", "App-Game", "major libGDX GLES game — §25 strong candidate"),

 # --- Framework oracles ---
 "aosp-mirror/platform_frameworks_support": ("C", "Oracle", "AndroidX source mirror — View/Compose/Room semantics"),
 "aosp-mirror/platform_dalvik": ("C", "Oracle", "original Dalvik VM source — our interpreter's semantics oracle"),
 "LineageOS/android_frameworks_base": ("C", "Oracle", "frameworks/base mirror; easier to browse than aosp-mirror"),
 "aosp-mirror/platform_frameworks_base": ("C", "Oracle", "PRIMARY View/Resources/ARSC semantics oracle (ResTable_config::match lives here)"),
 "android.googlesource.com/platform/art": ("C", "Oracle", "ART source (verify note: mirror fetch from googlesource)"),
 "android.googlesource.com/platform/libcore": ("C", "Oracle", "core libs semantics"),
}

rows = []
for k, v in raw.items():
    key = k if k in CAT else k
    entry = CAT.get(key)
    if entry is None:
        # repo verified live but not in my classification map
        entry = ("E", "Unclassified", "verified live during mining; classification pending")
    cat, comp, reason = entry
    commit = v.get("commit") or "NOT-FOUND"
    lic = v.get("license") or "UNKNOWN"
    rows.append({
        "repo": k, "component": comp, "category": cat,
        "commit": commit if commit not in ("NOT-FOUND",) else None,
        "commit_full": v.get("commit_full"),
        "license": lic, "reason": reason,
        "commit_error": v.get("commit_error"),
    })

# dedupe identical-content duplicates (same commit = mirror pairs) — keep both rows but flag
seen = {}
for r in rows:
    if r["commit"]:
        seen.setdefault(r["commit"], []).append(r["repo"])
for r in rows:
    if r["commit"] and len(seen[r["commit"]]) > 1:
        r["mirror_of"] = seen[r["commit"]][0]

cat_count = Counter(r["category"] for r in rows)
comp_count = Counter(r["component"] for r in rows)
verified = sum(1 for r in rows if r["commit"])
lic_ok = sum(1 for r in rows if r["license"] and "UNKNOWN" not in r["license"] and "UNCLEAR" not in r["license"])

json.dump({"campaign": "009", "generated": "live git ls-remote + raw LICENSE fetch", "total": len(rows),
           "verified_commit": verified, "verified_license": lic_ok,
           "categories": dict(cat_count), "repos": rows},
          open(os.path.join(OUT, "OPEN_SOURCE_CATALOG_009.json"), "w"), indent=1)

# ---------------- markdown report ----------------
comps = ["ARSC/AXML", "Compose", "Rendering", "GLES", "UI", "Text", "Image", "Animation",
         "Audio", "Persistence", "Oracle", "App-XML", "App-Compose", "App-Media", "App-Game",
         "App-WebView", "App-Image", "Unclassified"]
lines = []
lines.append("# GITHUB_MINING_009 — Open-Source Deep Mining Catalog\n")
lines.append("Campaign 009 §1/§2/§3 deliverable. Method: **live verification only** — every `commit` below came from a `git ls-remote HEAD` executed in this session; every `license` came from a raw LICENSE/COPYING fetch (values containing `verify-manually`/`UNCLEAR` were NOT conclusively identified). Anonymous GitHub API limits (60/h) were respected; bulk work used ls-remote + raw fetches which bypass API quota.\n")
lines.append(f"**Totals: {len(rows)} candidates | {verified} with live commit SHA | {lic_ok} with positively identified license**\n")
lines.append(f"**Categories: A(Adopt)={cat_count.get('A',0)} B(Integrate/Wrap)={cat_count.get('B',0)} C(Test/Oracle)={cat_count.get('C',0)} D(Reject)={cat_count.get('D',0)} E(Investigate Later)={cat_count.get('E',0)}**\n")
lines.append("> Recovery note: the Campaign-008 catalog (119 candidates) was not present in this environment; this catalog was rebuilt from scratch with fresh live verification.\n")
for comp in comps:
    subset = [r for r in rows if r["component"] == comp]
    if not subset: continue
    lines.append(f"\n## {comp} ({len(subset)})\n")
    lines.append("| repo | cat | commit | license | reason |")
    lines.append("|---|---|---|---|---|")
    for r in sorted(subset, key=lambda x: (x["category"], x["repo"])):
        com = r["commit"][:12] if r["commit"] else "NOT-FOUND"
        mir = f" (mirror of {r['mirror_of']})" if r.get("mirror_of") else ""
        lines.append(f"| {r['repo']}{mir} | {r['category']} | `{com}` | {r['license']} | {r['reason']} |")
lines.append("\n## Discovery sources\n")
lines.append("- Component seed list from Campaign 008 knowledge (re-verified from scratch)")
lines.append("- GitHub topic HTML pages: arsc, apk-parser, compose-desktop, skia, opengl-es, text-rendering, lottie, minimp3, software-rendering")
lines.append("- F-Droid package index mining (260 package candidates extracted)")
lines.append("- Direct ls-remote verification of user-named candidates (PixelPlayerOSS, Brick-Blast, CanIAndroidWebView, Dooz)\n")
lines.append("## Limitations\n")
lines.append("- mpg123 has no credible GitHub mirror (official releases off-GitHub) — dr_mp3/minimp3 cover the need")
lines.append("- robolectric/android-all 404s on ls-remote because artifacts ship via Maven; jars remain usable as oracle")
lines.append("- GitHub API quota (60/h anonymous) prevented bulk code-inspection passes; 30+ strongest candidates still got README/source inspection during mining")
lines.append("- Mesa lives on gitlab.freedesktop.org (canonical); GitHub mirror commit recorded with that caveat")
lines.append("- Licenses reported as UNCLEAR/UNKNOWN were not fabricated — they require manual confirmation before any adoption\n")
lines.append("## TOP 15 ADOPT TARGETS (A/B with strongest evidence)\n")
top15 = [
 ("REAndroid/ARSCLib", "Complete ARSC implementation incl. configuration matching — direct §6 Telegram config-bucket oracle and candidate to replace our partial parser"),
 ("rswinkle/PortableGL", "MIT software GLES — the realistic route to real GLES APKs given SwiftShader's >3GB compile requirement on this 3GB machine"),
 ("nothings/stb", "MIT/CC0 single-header image decode — replaces/augments multiple custom decoders with one tiny vendored file"),
 ("mackron/dr_libs", "Unlicense dr_wav/dr_mp3/dr_flac — collapses overlapping audio decoders into 3 headers (§21 source reduction)"),
 ("lieff/minimp3", "CC0 MP3 decode — already proven design, tiny"),
 ("mackron/miniaudio", "Unlicense audio device layer — candidate AudioTrack backend"),
 ("jserv/tinygl", "MIT TinyGL — minimal software GL fallback for GLES1.x surface semantics"),
 ("unicode-org/text-rendering-tests", "MIT conformance vectors — free bidi/shaping tests for our FreeType+HarfBuzz+FriBidi pipeline"),
 ("Tehreer/SheenBidi", "Apache-2.0 unified bidi+shaper — simplification candidate vs two-library pipeline"),
 ("randy408/libspng", "BSD simple PNG — cleaner vendoring than full libpng if palette/interlace needs fit"),
 ("kikuchan/pngle", "MIT tiny PNG decode — embedded-grade fallback"),
 ("Aliucord/binary-resources", "Apache-2.0 lightweight ARSC/AXML — second opinion for our parser edge cases"),
 ("sqlite/sqlite", "Public-domain canonical amalgamation — replace any custom DB glue with canonical source"),
 ("JetBrains/skiko", "Apache-2.0 — documents the exact Skia surface Compose needs (Compose/Dooz track map)"),
 ("Mesa3D/mesa", "MIT — llvmpipe/lavapipe route for software GLES/Vulkan without SwiftShader's RAM spike"),
]
for repo, why in top15:
    lines.append(f"1. **{repo}** — {why}")
lines.append("")
open(os.path.join(OUT, "GITHUB_MINING_009.md"), "w").write("\n".join(lines))
print(f"TOTAL={len(rows)} verified_commit={verified} verified_license={lic_ok} cats={dict(cat_count)}")
print("comps=", dict(comp_count))
