# HELPER_SOURCE_LIST — MiniAndroid Open-Source Source & Tool Intelligence

**HELPER_SOURCE_LIST.md — official permanent project artifact (GAME CHANGER pass, 2026-09-03).**
Provenance: created in response to the FINAL GAME CHANGER mission (PHASE 8–10); reviewed,
merged and re-prioritized by the GAME CHANGER pass itself (PHASE 9 self-review applied:
duplicates merged, low-value entries demoted to P3, missing important sources added).
Registered in: `MASTER_PROJECT_KNOWLEDGE.md` (§HELPER SOURCE INTELLIGENCE, K-43),
`KNOWLEDGE_LEDGER.csv` (LED-051), `KNOWLEDGE_RECONCILIATION.md` (§13).
Scope: every open-source project / library / tool / corpus / reference that can genuinely
make MiniAndroid better. Quality over quantity — nothing is here for being famous alone.

**Project context assumed by every entry**: MiniAndroid is an evidence-driven Android
compatibility runtime in C++17 that parses real APKs (ZIP/Manifest/ARSC/AXML), decodes DEX,
executes Dalvik bytecode on a register interpreter with Java-semantic bridges
(String/Integer/XmlPullParser/AtomicReference/InputStream...), inflates real view hierarchies,
renders software frames, and is validated by discriminating fixtures + pixel-golden laws.

---

## Legend

| Field | Meaning |
|---|---|
| TYPE | TOOL · LIBRARY · REFERENCE IMPLEMENTATION · CORPUS · TEST FRAMEWORK · DEBUGGING TOOL · RESEARCH PROJECT |
| USE DIRECTLY | link/depend/run as-is |
| PORT | adapt code into the repo |
| BORROW DESIGN | read + imitate architecture, not code |
| USE AS ORACLE | ground truth to diff our behavior against |
| USE FOR TESTING | harness/corpus/fuzzing role |
| USE FOR RESEARCH | background study |
| Priority | P0 = directly useful now · P1 = likely useful soon · P2 = useful later · P3 = reference only |

## 0. Already integrated (recorded here so nobody re-proposes them)

| Component | License | Role in MiniAndroid |
|---|---|---|
| zlib | zlib | APK central-directory + inflate |
| libpng / libjpeg-turbo / libwebp(+demux) | png / IJG / BSD | image decode chain (BitmapFactory path) |
| stb (stb_image) | MIT/PD | fallback image decode |
| FreeType | FTL/GPL2 | font rasterization |
| HarfBuzz | MIT/OldMIT | text shaping |
| FriBidi | LGPL-2.1+ | bidi algorithm |
| rlottie @4307553 | MIT | Lottie animation (Telegram parity; see Makefile EXP-097) |
| nlohmann/json | MIT | JSON persistence in tooling/tests |

### 0.1 Demo-APK toolchain (integrated 2026-09-04, `demo/`)

Used to build the real-APK execution proof without an Android SDK — the same
official components the Android build plugins wrap:

| Component | Version | License | Exact use | Why selected |
|---|---|---|---|---|
| Eclipse ECJ `org.eclipse.jdt:ecj` | 3.33.0 | EPL-2.0 | `java -jar ecj.jar -source 8 -target 8 -bootclasspath android-34.jar` compiles `demo/src/**.java` | runs on a JRE-only host (no JDK), supports `-bootclasspath` Android-style compilation |
| Google D8 (via `com.android.tools:r8`) | 8.13.23 | Apache-2.0 (AOSP) | `java -cp r8.jar com.android.tools.r8.D8 --release --lib android-34.jar` produces `classes.dex` | THE canonical Android dexer (AOSP); bytecode compatible with what real phones ship |
| android.jar (platform-34-ext7_r03) | API 34 | Apache-2.0 (AOSP) | compile-time platform stubs for ECJ + D8 `--lib` | official Google platform download, exact API surface apps are built against |

Evidence: `demo/build_demo_apk.sh`, `demo/README.md`, `docs/demo/EVIDENCE.md`.

---

## Part I — Runtime, Dalvik/DEX, ART, bytecode (categories 1–3, 21–24, 41–42)

### H-001 AOSP — `platform/art` (interpreter, verifier, dex)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: android.googlesource.com/platform/art (mirror: github.com/aosp-mirror/platform_art) · **License**: Apache-2.0 · **Language**: C++14/Java
- **Category**: 1 Android Runtime, 2 Dalvik/DEX, 3 ART, 23 bytecode, 42 interpreter technology
- **What it does**: The real Android runtime: `dex` (DEX file model), `interpreter/` (switch/threaded interpreters incl. `interpreter_switch_impl.cc`), verifier, mterp assembly core.
- **Why useful to MiniAndroid**: The single ground-truth oracle for opcode semantics, exception dispatch (find_catch), object model, monitor/Thread semantics, and DEX format edge cases. Every opcode question we had (K-37 lit8 shift, 35c/3rc nibbles, packed-switch payloads) has a canonical answer here.
- **Potential reuse**: USE AS ORACLE · **Potential adaptation**: PORT mterp's dispatch table organization ideas into `dalvik_engine.cpp`; borrow `CatchFinder` unwind order for K-09-hardening.
- **Expected gain**: HIGH · **Difficulty**: MEDIUM (huge codebase, C++14 vs our C++17 fine) · **Priority**: P0
- **Relevant files/modules**: `miniandroid/src/dex/dalvik_engine.{h,cpp}`, `dex_interpreter_batch.cpp`
- **Known limitations**: GPL... (no — Apache-2.0, clean); enormous; some paths assume oat/JIT artifacts absent in MiniAndroid.

### H-002 AOSP — `platform/libcore` + Apache Harmony legacy
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: android.googlesource.com/platform/libcore; harmony legacy inside git history · **License**: Apache-2.0 (libcore includes Apache Harmony-derived files, Guava, ICU4J)
- **Category**: 20 Java runtime, 21 JVM, 7 Android Framework
- **What it does**: Android's core libraries — the actual `java.lang`/`java.util`/`java.io` implementations our bridges imitate (Integer.parseInt range law K-41, String.substring SIOOBE K-20, Infinity/NaN words K-42).
- **Why useful**: The ONLY authoritative semantics source for bridge behavior. Harmony history additionally documents *why* (javadoc-level law, e.g. `Math.round` edge cases).
- **Potential reuse**: USE AS ORACLE · **Adaptation**: PORT javadoc contract lines into our bridge headers as comments.
- **Expected gain**: HIGH · **Difficulty**: LOW (read + extract contracts) · **Priority**: P0
- **Relevant files**: `dalvik_engine.cpp` bridge_to_api; `framework/android_shadows.cpp`

### H-003 smali / baksmali / dexlib2
- **TYPE**: TOOL + LIBRARY · **Source**: github.com/JesusFreke/smali · **License**: Apache-2.0 · **Language**: Java
- **Category**: 2 Dalvik/DEX, 23 bytecode, 24 reverse engineering, 55 test harnesses
- **What it does**: Canonical DEX disassembler/assembler + the most complete independent DEX read/write library (dexlib2).
- **Why useful**: Lets us hand-assemble *any* opcode sequence into a real DEX to build discriminating fixtures (the K-37 lesson: never trust a table derived from itself). Also an oracle for DEX format parsing edge cases (map_list, annotation offsets, 64-bit counts).
- **Potential reuse**: USE AS ORACLE + USE FOR TESTING (fixture factory) · **Adaptation**: script fixtures: smali → dx-less DEX → run in MiniAndroid → assert.
- **Expected gain**: HIGH · **Difficulty**: LOW (CLI) · **Priority**: P0
- **Relevant files**: `tests/semantic_*.cpp`, `miniandroid/scripts/`
- **Limitations**: Needs a JVM; smali syntax targets ART-era opcodes (fine).

### H-004 Apktool
- **TYPE**: TOOL · **Source**: github.com/iBotPeaches/Apktool · **License**: Apache-2.0 · **Language**: Java
- **Category**: 4 APK/AAB, 5 AXML, 6 ARSC/Resources, 45 ZIP/APK infrastructure
- **What it does**: Decodes/rebuilds APKs: AXML → text, ARSC → readable resources, smali back-assembly.
- **Why useful**: ORACLE for AXML/ARSC parsing: for any APK in our corpus, `apktool d` produces the ground-truth string pool / resource map / layout XML that our `arsc_parser.cpp`/`axml_parser.cpp` must agree with.
- **Potential reuse**: USE AS ORACLE · **Adaptation**: scripted differential test: our parse vs apktool dump on every corpus APK.
- **Expected gain**: HIGH (resource-family regressions die immediately) · **Difficulty**: LOW · **Priority**: P0
- **Relevant files**: `miniandroid/src/resources/{arsc_parser,axml_parser,resource_runtime}.cpp`
- **Limitations**: Java; occasionally chokes on deliberately malformed APKs (which is itself informative).

### H-005 Androguard
- **TYPE**: TOOL + LIBRARY · **Source**: github.com/androguard/androguard · **License**: Apache-2.0 (LGPL components) · **Language**: Python
- **Category**: 2 Dalvik/DEX, 4 APK, 38 APK corpus mining, 24 reverse engineering
- **What it does**: Python DEX/APK/ARSC/AXML analysis library + CLI (androguard analyze, apkid-like features).
- **Why useful**: Scriptable oracle for corpus-wide structural audits (K-37 was proven by a corpus opcode scan — Androguard does this in 5 lines instead of a hand-rolled C++ scanner).
- **Potential reuse**: USE FOR TESTING / corpus mining · **Adaptation**: wire into `scripts/` for periodic opcode/resource coverage reports.
- **Expected gain**: HIGH for audits · **Difficulty**: LOW · **Priority**: P0

### H-006 jadx
- **TYPE**: TOOL · **Source**: github.com/skylot/jadx · **License**: Apache-2.0 · **Language**: Java
- **Category**: 24 reverse engineering, 2 Dalvik/DEX, 38 corpus mining
- **What it does**: DEX→Java decompiler with GUI/CLI; excellent at recovering app logic from corpus APKs.
- **Why useful**: When a real APK misbehaves (dooz 69s timing, keyboard entry-chain), decompiled source explains which framework API the app actually calls — turning blind debugging into targeted shadow work.
- **Potential reuse**: USE FOR RESEARCH/DEBUGGING · **Expected gain**: MEDIUM-HIGH · **Difficulty**: LOW · **Priority**: P0

### H-007 Avian (lightweight JVM with DEX support)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: github.com/ReadyTalk/avian · **License**: Apache-2.0 · **Language**: C++
- **Category**: 21 JVM, 2 Dalvik/DEX, 42 interpreter technology
- **What it does**: A compact JVM in C++ that can execute DEX bytecode directly (openvm/dex paths) with a small class library.
- **Why useful**: The closest existing C++ sibling to MiniAndroid's core idea; its verifier design, exception tables, and GC object model are directly comparable engineering.
- **Potential reuse**: BORROW DESIGN · **Expected gain**: MEDIUM · **Difficulty**: MEDIUM · **Priority**: P1

### H-008 JamVM
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: jamvm.sourceforge.net (github.com/z2084jk/jamvm mirror) · **License**: GPL-2.0 · **Language**: C
- **Category**: 21 JVM, 42 interpreter technology
- **What it does**: An extremely small, readable JVM interpreter famous for clean code and threaded-code dispatch.
- **Why useful**: Best "read the whole VM in a weekend" reference for interpreter organization, monitor implementation, class loading states.
- **Potential reuse**: USE FOR RESEARCH / BORROW DESIGN (mind GPL: design only, no code lift) · **Expected gain**: MEDIUM · **Priority**: P1

### H-009 V8 Ignition (bytecode interpreter)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: github.com/v8/v8 (src/interpreter/) · **License**: BSD-3 (V8) · **Language**: C++
- **Category**: 42 interpreter technology, 41 compiler technology
- **What it does**: Chrome's register/accumulator-based bytecode interpreter; state-of-the-art dispatch (handlers generated from .tq/asm), bytecode-array builders, frame layout.
- **Why useful**: Dalvik and Ignition are both register machines; Ignition's generated-dispatch and operand-decode discipline is the modern playbook for our `execute_*` ladder.
- **Potential reuse**: BORROW DESIGN · **Expected gain**: MEDIUM (perf headroom documented in NOT_DONE) · **Difficulty**: MEDIUM · **Priority**: P2

### H-010 Lua VM (Lua 5.4)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: lua.org (gitlab) · **License**: MIT · **Language**: C
- **Category**: 42 interpreter technology
- **What it does**: The cleanest production register-VM ever shipped (~30k LOC core incl. compiler).
- **Why useful**: Exemplary patterns for register windows, try/unwind via longjmp-free design, tag values, upvalue handling — all mappable to Dalvik registers/objects.
- **Potential reuse**: BORROW DESIGN · **Expected gain**: MEDIUM · **Difficulty**: LOW · **Priority**: P1

### H-011 dex2jar / Enjarify
- **TYPE**: TOOL · **Source**: github.com/pxb1988/dex2jar (Apache-2.0); github.com/Storyyeller/enjarify (Apache-2.0) · **Language**: Java / Python
- **Category**: 2 Dalvik/DEX, 23 bytecode, 24 reverse engineering
- **What it does**: Translate DEX ↔ JVM bytecode, enabling the entire Java analysis ecosystem on our corpus.
- **Why useful**: Alternative semantic oracle: convert a corpus DEX to JVM class, run under OpenJDK, diff behavior against MiniAndroid (differential testing §7 Testing).
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM · **Priority**: P1
- **Limitations**: dex2jar struggles with obfuscated/edge DEX; Enjarify more robust but slower.

### H-012 Redex
- **TYPE**: TOOL · **Source**: github.com/facebook/redex · **License**: MIT · **Language**: C++
- **Category**: 2 Dalvik/DEX, 23 bytecode, 4 APK
- **What it does**: Facebook's DEX rewriter/optimizer pipeline (instrumentation passes included).
- **Why useful**: Industrial C++ DEX read/write with strict format coverage (cfg passes); its IR reveals DEX corner cases our parser must survive; its `instrument` pass = inspiration for coverage-instrumented fixtures.
- **Potential reuse**: BORROW DESIGN / USE FOR TESTING · **Expected gain**: MEDIUM · **Priority**: P2

---

## Part II — APK / AAB, AXML, ARSC, XML, ZIP (categories 4–6, 44–45)

### H-013 aapt2 (AOSP build tool)
- **TYPE**: TOOL · **Source**: android.googlesource.com/platform/frameworks/base/tools/aapt2 · **License**: Apache-2.0 · **Language**: C++
- **Category**: 4 APK/AAB, 5 AXML, 6 ARSC/Resources
- **What it does**: Google's resource compiler/packager — the program that *creates* every ARSC/AXML our parsers read.
- **Why useful**: Highest-authority oracle for resource table rules (type configs, dense entries, compact resources for API 33+). When `arsc_parser.cpp` meets a real table disagreement, aapt2 source settles it.
- **Potential reuse**: USE AS ORACLE · **Expected gain**: HIGH · **Difficulty**: MEDIUM (buildable standalone via AOSP soong or cmake ports) · **Priority**: P0

### H-014 expat
- **TYPE**: LIBRARY · **Source**: github.com/libexpat/libexpat · **License**: MIT · **Language**: C
- **Category**: 44 XML, 7 Android Framework
- **What it does**: The streaming XML parser Android itself uses (ExpatPullParser lineage) — battle-tested event semantics.
- **Why useful**: K-34 built our XmlPullParser event machine; expat's event model + error cases (malformed UTF-8, entity recursion, premature EOF) are the exact hardening checklist for `xml_shadow`/pull-parser parity.
- **Potential reuse**: USE DIRECTLY (optional backend) or USE AS ORACLE · **Expected gain**: MEDIUM-HIGH · **Difficulty**: LOW · **Priority**: P1
- **Relevant files**: `framework/android_shadows.cpp` (XmlPullParser), tests/semantic_pass3_bridge_test.cpp [GROUP X]

### H-015 pugixml
- **TYPE**: LIBRARY · **Source**: zeux.io/projects/pugixml (github.com/zeux/pugixml) · **License**: MIT · **Language**: C++
- **Category**: 44 XML
- **What it does**: Fast DOM XPath XML parser.
- **Why useful**: AXML post-parse tree manipulation and test assertions (view-tree JSON comparison) get easier with a solid DOM; P2 because AXML is binary and our SAX-style flow already works.
- **Potential reuse**: USE DIRECTLY (tests only) · **Expected gain**: LOW-MEDIUM · **Priority**: P2

### H-016 miniz
- **TYPE**: LIBRARY · **Source**: github.com/richgel999/miniz · **License**: MIT · **Language**: C
- **Category**: 45 ZIP/APK infrastructure
- **What it does**: Single-file ZIP reader/writer + deflate, used by many emulators/tools.
- **Why useful**: A tiny reference cross-check for our zlib-based APK parser — especially for malformed central directories (data-descriptor flags, zip64, alignment paddings produced by real build tools like zipalign).
- **Potential reuse**: USE FOR TESTING (malformed-ZIP generator reference) · **Expected gain**: LOW-MEDIUM · **Priority**: P2

### H-017 LIEF
- **TYPE**: LIBRARY · **Source**: lief.re (github.com/lief-project/LIEF) · **License**: Apache-2.0 · **Language**: C++/Python
- **Category**: 4 APK, 25 binary analysis, 26 disassembly
- **What it does**: Parse/modify ELF/PE/Mach-O — including the native `.so` libraries inside APKs.
- **Why useful**: Native-lib manifests (`extractNativeLibs`), JNI surface enumeration, and future JNI bridge work all need ELF understanding without writing our own.
- **Potential reuse**: USE DIRECTLY (tooling) / BORROW DESIGN · **Expected gain**: MEDIUM (unlocks native-lib lane documented in NOT_DONE) · **Priority**: P1

---

## Part III — Android Framework, UI, text (categories 7–8, 46)

### H-018 AOSP — `platform/frameworks/base`
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: android.googlesource.com/platform/frameworks/base (github.com/aosp-mirror/platform_frameworks_base) · **License**: Apache-2.0 · **Language**: Java/Kotlin/C++
- **Category**: 7 Android Framework, 8 Android UI
- **What it does**: The real View/TextView/Button/EditText/Dialog/Toast/ArrayAdapter/Activity/Window classes, `LayoutInflater`, measure/layout/draw passes, input pipeline, resource resolution (`ResourcesImpl`, `AssetManager2`).
- **Why useful**: The definitive behavioral oracle for every shadow in `android_shadows.cpp` (hierarchy shadow dispatch, real-tree inflation, click dispatch) and for `layout_inflater.cpp` (`parseLayoutAttribute`, theme chains).
- **Potential reuse**: USE AS ORACLE · **Adaptation**: PORT specific contracts (measure spec math, `View.post` queue semantics) into shadow comments + fixtures.
- **Expected gain**: HIGH · **Difficulty**: MEDIUM (huge; navigate via cs.android.com) · **Priority**: P0

### H-019 Robolectric
- **TYPE**: TEST FRAMEWORK · **Source**: github.com/robolectric/robolectric · **License**: MIT · **Language**: Java
- **Category**: 8 Android UI, 55 test harnesses, 7 Framework
- **What it does**: Runs real Android framework code on the JVM by *shadowing* the native/framework layer — the same architectural trick as MiniAndroid, in a different language, with 15 years of accumulated shadow semantics.
- **Why useful**: Its `org.robolectric.shadows` package is a giant annotated catalog of expected framework behaviors (ShadowView, ShadowTextView, ShadowToast, ShadowHandler...) including gnarly corner rules we keep rediscovering (post-at-front-of-queue, invalidated-layout-on-attach...).
- **Potential reuse**: USE AS ORACLE (primary!) + BORROW DESIGN (shadow registry concept — we already have `shadow_registry.cpp`, theirs validates our taxonomy) · **Expected gain**: HIGH · **Difficulty**: LOW (read source; running needs JVM+Maven) · **Priority**: P0
- **Limitations**: Java-only execution; some shadows target Robolectric's own test needs, not law.

### H-020 AndroidX source (appcompat / recyclerview / core)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: android.googlesource.com/platform/frameworks/support · **License**: Apache-2.0 · **Language**: Java/Kotlin
- **Category**: 8 Android UI, 7 Framework
- **What it does**: The compatibility libraries most corpus apps actually ship (AppCompat activity/dialog theming, RecyclerView recycling).
- **Why useful**: Corpus apps (chessclock/headingcalculator era) embed AndroidX classes in their DEX — our runtime executes AndroidX code, so its source is the oracle for what app-shipped framework code expects from *our* shadows.
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM-HIGH · **Priority**: P1

### H-021 ICU4C
- **TYPE**: LIBRARY · **Source**: github.com/unicode-org/icu · **License**: ICU License (MIT-compatible) · **Language**: C/C++
- **Category**: 46 font/text, 20 Java runtime, 7 Framework
- **What it does**: Unicode engine Android links for String.toUpperCase, collation, number formatting, Calendar — the law behind dozens of `java.lang/String.format` behaviors our bridges must match.
- **Why useful**: Every text-bridge discrepancy trace (e.g. locale-dependent casing in corpus apps) terminates at ICU; either link it or port per-case rules.
- **Potential reuse**: USE DIRECTLY (heavy) or USE AS ORACLE (light) · **Expected gain**: MEDIUM (grows with app diversity) · **Difficulty**: MEDIUM (size) · **Priority**: P1

### H-022 utf8proc
- **TYPE**: LIBRARY · **Source**: github.com/JuliaStrings/utf8proc · **License**: MIT · **Language**: C
- **Category**: 46 font/text
- **What it does**: Small, clean Unicode normalization/case/width tables.
- **Why useful**: Lightweight alternative to ICU for String-level bridges (Character.isXxx, toUpperCase(null-locale)) when full ICU is too heavy.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: LOW-MEDIUM · **Priority**: P2

---

## Part IV — Rendering, Skia, GLES/Vulkan, image, SVG, animation, rlottie (categories 9–16)

### H-023 Skia
- **TYPE**: LIBRARY · **Source**: skia.org (chromium.googlesource.com/skia) · **License**: BSD-3 · **Language**: C++
- **Category**: 10 Skia, 9 Rendering, 14 SVG (via SVG module), 13 Image decoding
- **What it does**: Android's actual 2D engine: Canvas/Paint semantics, paths, region ops, color filters, shaders, raster pipeline.
- **Why useful**: The canonical oracle for `canvas_shadow.cpp` + `software_renderer.cpp`: clip-save/restore, matrix composition order (RESULT_014 partial!), Porter-Duff blend modes, antialiasing rules. Golden-screenshot discrepancies that resist analysis end here.
- **Potential reuse**: USE AS ORACLE (primary) · **Adaptation**: optionally USE DIRECTLY as a *comparison renderer* in differential mode (not replacing our renderer — validating it). **Expected gain**: HIGH · **Difficulty**: MEDIUM (build is well-supported) · **Priority**: P0
- **Known limitations**: building full Skia is heavyweight; the *oracle use* only needs its public API + our own driver.

### H-024 Cairo
- **TYPE**: LIBRARY · **Source**: cairographics.org · **License**: LGPL-2.1 (MPL variant for parts) · **Language**: C
- **Category**: 9 Rendering
- **What it does**: Mature software vector rasterizer (paths, AA, compositor).
- **Why useful**: Alternative reference rasterizer algorithms (stroker/tessellator) where our `software_renderer.cpp` lacks precision (arc/round-rect quality gaps seen in bgclock golden history).
- **Potential reuse**: BORROW DESIGN (LGPL — keep at arm's length or link dynamically) · **Expected gain**: MEDIUM · **Priority**: P2

### H-025 Blend2D
- **TYPE**: LIBRARY · **Source**: blend2d.com (github.com/blend2d/blend2d) · **License**: zlib · **Language**: C++
- **Category**: 9 Rendering, 10 Skia-alternative
- **What it does**: Modern high-performance 2D rasterizer with JIT pipelining; permissive license.
- **Why useful**: zlib-licensed Skia-grade rasterization if we ever swap engines; also an independent differential renderer for golden disputes.
- **Potential reuse**: USE DIRECTLY (differential mode) · **Expected gain**: MEDIUM · **Priority**: P2

### H-026 NanoSVG
- **TYPE**: LIBRARY · **Source**: github.com/memononen/nanosvg · **License**: zlib · **Language**: C
- **Category**: 14 SVG, 9 Rendering
- **What it does**: Single-header SVG parser + rasterizer.
- **Why useful**: Android VectorDrawable is SVG-shaped; NanoSVG's path/gradient parsing is a compact reference (and potential filler) for our vector-drawable support lane.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM (vector drawables appear in modern corpus APKs) · **Priority**: P1

### H-027 resvg
- **TYPE**: TOOL/LIBRARY · **Source**: github.com/linebender/resvg · **License**: Apache-2.0/MIT · **Language**: Rust
- **Category**: 14 SVG, 13 image
- **What it does**: The most correct SVG renderer available; strict conformance.
- **Why useful**: Oracle for VectorDrawable/SVG semantics (does our inflation render the same icon as the law says?).
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM · **Priority**: P2 (needs Rust toolchain)

### H-028 Lottie / lottie-android + lottie-web
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: github.com/airbnb/lottie-android (Apache-2.0), github.com/airbnb/lottie-web (MIT) · **Language**: Java / JS
- **Category**: 15 Animation, 16 rlottie
- **What it does**: The animation format ecosystem around rlottie; lottie-web is the reference interpreter for edge behaviors.
- **Why useful**: We ship rlottie for Telegram parity; when a Lottie animation misbehaves, lottie-web is the semantic oracle above rlottie itself.
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM · **Priority**: P2

### H-029 libyuv
- **TYPE**: LIBRARY · **Source**: chromium.googlesource.com/libyuv (github.com/lemenkov mirror) · **License**: BSD-3 · **Language**: C++
- **Category**: 13 Image decoding, 9 Rendering
- **What it does**: YUV↔RGB conversion, scaling, rotate — the pixel-format workhorse Android video/camera paths use.
- **Why useful**: Screenshots/bitmaps from corpus apps with camera/video surfaces will need exact YUV semantics; also useful for our screenshot pipeline optimization.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: LOW-MEDIUM · **Priority**: P2

### H-030 GLES moonlight-unit / Mesa (reference GLES implementation)
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: mesa.freedesktop.org (gitlab.freedesktop.org/mesa/mesa) · **License**: MIT-family (per-component) · **Language**: C/C++
- **Category**: 11 OpenGL/GLES, 12 Vulkan, 9 Rendering
- **What it does**: Open-source GL/GLES/Vulkan stack; llvmpipe = software GLES oracle.
- **Why useful**: Our GLES hook is documented (NOT_DONE / GLES_REPORT_013); llvmpipe gives a *lawful software GLES* to diff any future GLES shadow against.
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM (when GLES lane opens) · **Difficulty**: HIGH · **Priority**: P2

---

## Part V — Emulator, headless Android, Linux compatibility (categories 17–19, 50–51)

### H-031 Wine
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: winehq.org (gitlab.winehq.org/wine/wine) · **License**: LGPL-2.1 · **Language**: C
- **Category**: 19 Linux Android compatibility, 50 process/runtime isolation, 7 Framework
- **What it does**: 30-year-old Windows API compatibility layer on Linux — the deepest existing record of "reimplement a platform API so real apps run".
- **Why useful**: The best cross-domain teacher for the exact problems MiniAndroid faces: API surface archaeology, versioned quirks per app, regression discipline via per-app test databases (Wine's conformance tests are a model for our fixture philosophy).
- **Potential reuse**: USE FOR RESEARCH + BORROW DESIGN (conformance-test organization; bug-for-bug compatibility documentation style) · **Expected gain**: HIGH (methodology transfer) · **Priority**: P1

### H-032 Waydroid / Anbox lineage
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: docs.waydro.id (github.com/waydroid) · **License**: GPL-3.0 · **Language**: C/Python
- **Category**: 17 Emulator, 18 Headless Android, 19 Linux compatibility
- **What it does**: Full real Android (system image) in an LXC container on Linux — real ART, real SurfaceFlinger.
- **Why useful**: (a) *Differential oracle machine*: run any corpus APK under real ART headlessly, screenshot, diff vs MiniAndroid; (b) architectural map of which Android subsystems an APK really touches.
- **Potential reuse**: USE AS ORACLE (differential testing §7) · **Expected gain**: HIGH for the testing program · **Difficulty**: MEDIUM (needs kernel modules/zabb); container-friendly CI images exist · **Priority**: P1

### H-033 Android-x86 / BlissOS
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: android-x86.org · **License**: Apache-2.0 (Android base) · **Language**: mixed
- **Category**: 17 Emulator, 19 Linux compatibility
- **What it does**: Android running natively on PC hardware.
- **Why useful**: x86 Android images = fastest real-runtime oracle (qemu/KVM) for differential screenshots without ARM translation.
- **Potential reuse**: USE FOR TESTING · **Expected gain**: MEDIUM · **Priority**: P2

### H-034 QEMU
- **TYPE**: TOOL · **Source**: qemu.org (gitlab.com/qemu-project/qemu) · **License**: GPL-2.0 · **Language**: C
- **Category**: 17 Emulator, 42 interpreter technology (TCG design)
- **What it does**: The system emulator; TCG = the reference dynamic binary translator.
- **Why useful**: Headless corpus execution at scale (oracle screenshots, fuzz seeds); TCG is the textbook for any future JIT lane.
- **Potential reuse**: USE DIRECTLY (test infra) · **Expected gain**: MEDIUM · **Priority**: P2

### H-035 gVisor / nsjail
- **TYPE**: TOOL · **Source**: github.com/google/gvisor (Apache-2.0); github.com/google/nsjail (Apache-2.0) · **Language**: Go/C
- **Category**: 51 sandboxing, 50 process/runtime isolation
- **What it does**: Application sandboxing (syscall interception / namespace jail).
- **Why useful**: Running untrusted corpus APKs through our runtime in CI without trusting our own parser's robustness (fuzzing crashes stay contained).
- **Potential reuse**: USE DIRECTLY (CI) · **Expected gain**: MEDIUM · **Priority**: P2

---

## Part VI — Testing: fuzzing, differential, property, screenshots, UI automation (categories 27–33, 55–58)

### H-036 libFuzzer + AFL++
- **TYPE**: TOOL · **Source**: llvm.org docs (github.com/llvm/llvm-project); github.com/AFLplusplus/AFLplusplus (Apache-2.0) · **Language**: C++ / C
- **Category**: 27 fuzzing, 55 test harnesses, 58 fuzz corpus
- **What it does**: Coverage-guided fuzzing engines.
- **Why useful**: Our parsers (DEX/ARSC/AXML/ZIP/manifest) are exactly the attack surface fuzzers live on; libFuzzer runs in-process with our existing C++ objects (a `LLVMFuzzerTestOneInput` shim over `apk_parser`/`arsc_parser` is ~50 LOC); AFL++ covers the same externally.
- **Potential reuse**: USE DIRECTLY · **Adaptation**: crash corpus → regression fixtures (our fixture pattern already consumes crash seeds well) · **Expected gain**: HIGH (robustness) · **Difficulty**: LOW-MEDIUM · **Priority**: P0
- **Relevant files**: `src/apk/*`, `src/resources/*`, `src/dex/dex_parser.cpp`

### H-037 GoogleTest / doctest / Catch2
- **TYPE**: TEST FRAMEWORK · **Source**: github.com/google/googletest (BSD-3); github.com/doctest/doctest (MIT); github.com/catchorg/Catch2 (BSL-1.0) · **Language**: C++
- **Category**: 55 test harnesses, 56 corpus management
- **What it does**: Standard C++ assertion/registration frameworks.
- **Why useful**: Our fixtures are excellent but hand-rolled (PASS/FAIL line counting); migrating to doctest (header-only, MIT) gives us per-case names, filters, fatal/non-fatal asserts, and XML reports with almost no weight.
- **Potential reuse**: USE DIRECTLY (new fixtures; gradual migration) · **Expected gain**: MEDIUM (test ergonomics, fewer false-greens) · **Difficulty**: LOW · **Priority**: P1

### H-038 rapidcheck
- **TYPE**: TEST FRAMEWORK · **Source**: github.com/emil-e/rapidcheck · **License**: BSD-2 · **Language**: C++
- **Category**: 28 differential testing, 29 property testing
- **What it does**: QuickCheck-style property-based testing for C++.
- **Why useful**: Properties like "for any int pair, our div matches JVM semantics", "for any well-formed ARSC, our resolver == aapt2's answer" express the K-41/K-37 class of bugs generically.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM-HIGH · **Difficulty**: LOW-MEDIUM · **Priority**: P1

### H-039 Hypothesis
- **TYPE**: TEST FRAMEWORK · **Source**: github.com/HypothesisWorks/hypothesis · **License**: MPL-2.0 · **Language**: Python
- **Category**: 29 property testing, 38 corpus mining
- **What it does**: The best property-testing engine (shrinking, states, ghosts) for Python test drivers.
- **Why useful**: Our test drivers are already Python (`scripts/exp*.py`); Hypothesis can generate mutated-DEX/ARSC corpora + shrink failing cases into minimal fixtures automatically.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM-HIGH · **Difficulty**: LOW · **Priority**: P1

### H-040 pixelmatch (screenshot diff reference)
- **TYPE**: TOOL · **Source**: github.com/mapbox/pixelmatch · **License**: ISC · **Language**: JS
- **Category**: 30 screenshot testing, 31 visual regression
- **What it does**: Perceptual pixel-diff algorithm (anti-aliased pixels excluded, color-distance threshold).
- **Why useful**: Our goldens are SHA-equality (perfect) but we also need *diagnosis* diffs (where did the frame change?); pixelmatch's algorithm is small enough to port to the C++ evidence tools.
- **Potential reuse**: PORT (into `tools/` screenshot-diff) · **Expected gain**: MEDIUM · **Priority**: P2

### H-041 SSIM / OpenCV
- **TYPE**: LIBRARY · **Source**: github.com/opencv/opencv · **License**: Apache-2.0 · **Language**: C++
- **Category**: 31 visual regression, 9 Rendering
- **What it does**: Image analysis incl. SSIM, template matching, contour metrics.
- **Why useful**: For non-golden corpus apps (no pinned SHA), SSIM gives a principled "same picture" measure for cross-version regression reports.
- **Potential reuse**: USE DIRECTLY (tools only) · **Expected gain**: MEDIUM · **Priority**: P2

### H-042 Frida
- **TYPE**: DEBUGGING TOOL · **Source**: frida.re (github.com/frida/frida) · **License**: wxWindows (LGPL-like) · **Language**: C/JS/Python
- **Category**: 34 debugging, 35 tracing, 28 differential testing
- **What it does**: Dynamic instrumentation of live processes (real Android included) — inject JS to trace any method call.
- **Why useful**: The bridge to ground truth on a REAL device/emulator: trace how a corpus app's method actually behaves under ART (arguments, return, exceptions) and encode that as a fixture for MiniAndroid. Turns "we think ART does X" into recorded evidence.
- **Potential reuse**: USE AS ORACLE (with Waydroid H-032 or any device) · **Expected gain**: HIGH for compatibility disputes · **Difficulty**: MEDIUM · **Priority**: P1

### H-043 UI Automator / Espresso (behavior oracles)
- **TYPE**: TEST FRAMEWORK · **Source**: android.googlesource.com/platform/frameworks/uiautomator + androidx.test.espresso · **License**: Apache-2.0 · **Language**: Java
- **Category**: 32 UI automation, 33 input simulation, 8 UI
- **What it does**: Android's own UI event dispatch tests and automation APIs.
- **Why useful**: Authoritative event-dispatch semantics (touch→click→long-click ordering, focus, IME interplay) for our hierarchy dispatch and `--click-test` lane.
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM · **Priority**: P2

### H-044 Android CTS
- **TYPE**: CORPUS + TEST FRAMEWORK · **Source**: android.googlesource.com/platform/cts · **License**: Apache-2.0 · **Language**: Java
- **Category**: 57 differential oracle, 55 test harnesses, 7 Framework
- **What it does**: Google's Compatibility Test Suite — thousands of framework-behavior tests (CTS for `java.lang`, View, resources...).
- **Why useful**: A pre-written catalog of *behavioral laws* with expected values; CtsMediaTest/CtsViewTestCases cases translate directly into our fixture style (pick a case, port the assertion, run).
- **Potential reuse**: USE AS ORACLE + fixture-mining · **Expected gain**: HIGH (leverage) · **Difficulty**: MEDIUM (huge; needs triage) · **Priority**: P1

### H-045 diffoscope
- **TYPE**: TOOL · **Source**: diffoscope.org (salsa.debian.org/reproducible-builds/diffoscope) · **License**: GPL-3.0 · **Language**: Python
- **Category**: 28 differential testing, 54 reproducible builds
- **What it does**: In-depth recursive diff of any two files/archives (ZIPs, APKs, JSON, images...).
- **Why useful**: Explains *why* two runs/screenshots/APKs differ at every level — ideal for reproducibility investigations (dooz timing anomaly class).
- **Potential reuse**: USE DIRECTLY (tooling) · **Expected gain**: MEDIUM · **Priority**: P2

---

## Part VII — Debugging, tracing, profiling, memory, RE (categories 34–37)

### H-046 AddressSanitizer / UBSan / TSan
- **TYPE**: DEBUGGING TOOL · **Source**: ships with GCC/Clang · **License**: LLVM/GCC runtime exceptions · **Language**: N/A
- **Category**: 34 debugging, 37 memory analysis
- **What it does**: Compiler-instrumented memory/UB/thread error detection.
- **Why useful**: A `-fsanitize=address,undefined` build of the engine over the fixture+corpus suite is the cheapest deep bug-hunt we can run; the DEX interpreter walks attacker-shaped data (corpus APKs) daily.
- **Potential reuse**: USE DIRECTLY (CI variant target in Makefile) · **Expected gain**: HIGH · **Difficulty**: LOW · **Priority**: P0

### H-047 Valgrind
- **TYPE**: DEBUGGING TOOL · **Source**: valgrind.org · **License**: GPL-2.0 · **Language**: C
- **Category**: 37 memory analysis, 35 tracing
- **What it does**: Gold-standard memory/leak/undefined-value analysis without recompiling.
- **Why useful**: Cross-checks ASan and catches uninitialized reads in resource parsing paths ASan might pattern-match differently.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM · **Priority**: P2

### H-048 perf + FlameGraph
- **TYPE**: DEBUGGING TOOL · **Source**: perf.wiki.kernel.org; github.com/brendangregg/FlameGraph (GPL/SPL) · **Language**: C/awk
- **Category**: 36 profiling, 35 tracing
- **What it does**: Linux profiling + the standard flamegraph visualization.
- **Why useful**: dooz 69.9s-under-load vs 0.8s-idle anomaly (K-33) deserves flamegraphs; any "runtime is slow" claim becomes evidence.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM · **Priority**: P1

### H-049 heaptrack
- **TYPE**: DEBUGGING TOOL · **Source**: github.com/KDE/heaptrack · **License**: LGPL-2.1 · **Language**: C++
- **Category**: 37 memory analysis, 36 profiling
- **What it does**: Heap allocation profiler with flamegraph UI.
- **Why useful**: Frame rendering allocates heavily (buffers, bitmaps); heaptrack finds retention bugs before they become OOM in long app runs.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: LOW-MEDIUM · **Priority**: P2

### H-050 Ghidra
- **TYPE**: DEBUGGING TOOL · **Source**: ghidra-sre.org (github.com/NationalSecurityAgency/ghidra) · **License**: Apache-2.0 · **Language**: Java
- **Category**: 25 reverse engineering, 26 disassembly, 24 binary analysis
- **What it does**: NSA's full RE workbench; DEX loaders included.
- **Why useful**: When corpus DEX defeats jadx (H-006), Ghidra's DEX analysis + decompiler is the fallback; also headless scripting for corpus triage.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM · **Priority**: P2

### H-051 radare2 / rizin
- **TYPE**: DEBUGGING TOOL · **Source**: github.com/radareorg/radare2 (LGPL-3.0); github.com/rizinorg/rizin (LGPL-3.0) · **Language**: C
- **Category**: 26 disassembly, 24 binary analysis
- **What it does**: Scriptable binary analysis CLIs incl. DEX/ZIP formats.
- **Why useful**: Scriptable format poking during parser debugging (faster than writing one-off C++ probes).
- **Potential reuse**: USE DIRECTLY · **Expected gain**: LOW-MEDIUM · **Priority**: P3

---

## Part VIII — Corpus, API/resource mining, Java runtime infrastructure (categories 38–40, 20–22, 47–49, 52–54, 59–60)

### H-052 F-Droid
- **TYPE**: CORPUS · **Source**: f-droid.org (gitlab.com/fdroid/fdroiddata) · **License**: AGPL-3.0 (server/index); apps are FOSS with their own licenses · **Language**: N/A
- **Category**: 38 APK corpus mining, 59 Android compatibility projects
- **What it does**: The FOSS Android app store with a full buildable index of APKs per version.
- **Why useful**: The *legal, reproducible* APK corpus source for MiniAndroid (our zero-APK repo policy + `download_test_apks.py` architecture fits it exactly); per-app version pinning beats upstream-link rot (the Telegram golden loss, K-26).
- **Potential reuse**: USE DIRECTLY (corpus acquisition; pin versions in `APK_REGISTRY.json`) · **Expected gain**: HIGH · **Difficulty**: LOW · **Priority**: P0
- **Limitations**: package set is FOSS-only; big apps (Telegram) arrive via build metadata, not direct store links.

### H-053 AndroZoo
- **TYPE**: CORPUS · **Source**: androzoo.org · **License**: academic access agreement · **Language**: N/A
- **Category**: 38 APK corpus mining
- **What it does**: 20M+ APK research corpus with metadata (VirusTotal flags, market provenance).
- **Why useful**: For *diversity* campaigns (obfuscated/hybrid apps stress the interpreter beyond F-Droid's clean FOSS apps); API key required.
- **Potential reuse**: USE FOR TESTING (research lane) · **Expected gain**: MEDIUM · **Priority**: P2

### H-054 apkeep
- **TYPE**: TOOL · **Source**: github.com/EFForg/apkeep · **License**: GPL-3.0 · **Language**: Rust
- **Category**: 38 APK corpus mining, 60 utilities
- **What it does**: Downloads APKs from multiple sources (APKPure, F-Droid, Google Play via credentials) with version pinning.
- **Why useful**: Hardens `download_test_apks.py` (single-source today); version-pinned fetches fix the corpus data-loss class (K-26).
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM · **Priority**: P1

### H-055 OpenJDK
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: github.com/openjdk/jdk · **License**: GPL-2.0-with-classpath-exception · **Language**: Java/C++
- **Category**: 20 Java runtime, 21 JVM, 28 differential testing
- **What it does**: The reference Java implementation.
- **Why useful**: (a) law checks beyond libcore; (b) `enjarify`-converted corpus methods can be executed under OpenJDK and diffed against MiniAndroid (differential harness H-011).
- **Potential reuse**: USE AS ORACLE · **Expected gain**: MEDIUM · **Priority**: P1

### H-056 JNI spec + AOSP `libnativehelper`
- **TYPE**: REFERENCE IMPLEMENTATION · **Source**: docs.oracle.com/javase/8/docs/technotes/guides/jni/spec; android.googlesource.com/platform/libnativehelper · **License**: Apache-2.0 (AOSP) · **Language**: C/C++
- **Category**: 22 JNI, 7 Framework
- **What it does**: The JNI contract + AOSP's helper layer (scoped refs, exception checks).
- **Why useful**: Any future native-lib/JNI lane must implement this contract exactly; libnativehelper shows the hygiene patterns (local/global refs, pending exceptions).
- **Potential reuse**: USE AS ORACLE / BORROW DESIGN · **Expected gain**: MEDIUM (when JNI lane opens) · **Priority**: P2

### H-057 API harvesting: androidx.platform/tools-apifinder + hidden-api lists
- **TYPE**: CORPUS + TOOL · **Source**: android.googlesource.com/platform/tools/apifinder; github.com/aosp-mirror/platform_frameworks_base (hidden-api lists maintained by community forks e.g. github.com/Ghzgar/hidden-api-lists) · **License**: Apache-2.0 · **Language**: Java/text
- **Category**: 39 API mining, 7 Framework
- **What it does**: Machine-readable catalog of every public/hidden Android API per version.
- **Why useful**: Directly feeds our shadow registry coverage metric: which APIs do corpus DEXs actually reference vs which our `android_shadows.cpp` implements (the gap matrix, automated).
- **Potential reuse**: USE DIRECTLY (coverage reporting) · **Expected gain**: HIGH (turns gap matrix from manual to computed) · **Difficulty**: LOW-MEDIUM · **Priority**: P1

### H-058 protobuf + flatbuffers
- **TYPE**: LIBRARY · **Source**: github.com/protocolbuffers/protobuf (BSD-3); github.com/google/flatbuffers (Apache-2.0) · **Language**: C++
- **Category**: 43 serialization, 4 APK
- **What it does**: The serialization systems Android uses (protobuf in system services; flatbuffers for some system formats).
- **Why useful**: Modern Android artifacts (Play-delivered split APK metadata, some manifest-adjacent blobs) embed these; parser readiness avoids the next "unknown binary blob" dead-end.
- **Potential reuse**: USE DIRECTLY (tooling) · **Expected gain**: LOW-MEDIUM · **Priority**: P3

### H-059 ccache
- **TYPE**: TOOL · **Source**: ccache.dev (github.com/ccache/ccache) · **License**: GPL-3.0 · **Language**: C++
- **Category**: 53 CI, 60 utilities
- **What it does**: Compiler cache.
- **Why useful**: Our full rebuild is minutes; every validation pass rebuilds; ccache makes CI-grade validation loops fast (directly supports the ×3 reproducibility rule).
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM (velocity) · **Priority**: P1

### H-060 GitHub Actions
- **TYPE**: TOOL · **Source**: github.com/features/actions; actions/runner · **License**: proprietary service (runner MIT) · **Language**: YAML
- **Category**: 52 CI, 53 GitHub Actions
- **What it does**: Hosted CI.
- **Why useful**: Encode the GAME CHANGER validation (build + 144 fixtures + goldens ×3 + ARSC + click) as a workflow so every future commit re-proves the golden law — the exact discipline that caught K-37.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: HIGH (process) · **Priority**: P1
- **Note**: runner needs libwebp/jpeg/freetype/harfbuzz/fribidi apt packages + rlottie build step (documented in Makefile).

### H-061 Reproducible Builds (SOURCE_DATE_EPOCH tooling)
- **TYPE**: REFERENCE · **Source**: reproducible-builds.org (github.com/reproducible-builds/reproducible-*) · **License**: MIT (docs/tools) · **Language**: N/A
- **Category**: 54 reproducible builds
- **What it does**: Standards + tools for byte-reproducible artifacts.
- **Why useful**: Our handoffs must stay byte-identical across machines (golden law for *builds*, not just screenshots); the tools (ar-epoch, zipclamp) formalize it.
- **Potential reuse**: BORROW DESIGN / USE DIRECTLY · **Expected gain**: MEDIUM · **Priority**: P2

### H-062 mbedTLS / BoringSSL
- **TYPE**: LIBRARY · **Source**: github.com/Mbed-TLS/mbedtls (Apache-2.0); boringssl.googlesource.com (Apache/OpenSSL hybrid) · **Language**: C
- **Category**: 48 crypto compatibility, 47 networking compatibility
- **What it does**: TLS stacks (mbedTLS = embeddable; BoringSSL = Android's actual).
- **Why useful**: Corpus apps that open HTTPS (droidify family) will need java.net/crypto shadows backed by a real TLS stack when the networking lane opens.
- **Potential reuse**: USE DIRECTLY (later) · **Expected gain**: MEDIUM (lane-gated) · **Priority**: P2

### H-063 libcurl
- **TYPE**: LIBRARY · **Source**: curl.se (github.com/curl/curl) · **License**: curl (MIT-like) · **Language**: C
- **Category**: 47 networking compatibility
- **What it does**: The universal HTTP client library.
- **Why useful**: Same lane as H-062: HttpURLConnection/OkHttp shadows eventually bottom out in a real HTTP engine.
- **Potential reuse**: USE DIRECTLY (later) · **Expected gain**: MEDIUM (lane-gated) · **Priority**: P2

### H-064 Dolphin / RPCS3 (interpreter engineering references)
- **TYPE**: RESEARCH PROJECT · **Source**: github.com/dolphin-emu/dolphin (GPL-2.0); github.com/RPCS3/rpcs3 (GPL-2.0) · **Language**: C++
- **Category**: 42 interpreter technology, 17 Emulator
- **What it does**: Two of the most successful emulator projects alive; exceptional interpreter/JIT/recompiler engineering with per-instruction verification cultures.
- **Why useful**: Their discipline (instruction tables generated from verified specs, per-instruction unit tests, golden-frame comparisons) is the engineering culture MiniAndroid's fixture philosophy is converging toward; reading their handler structure pays off directly.
- **Potential reuse**: USE FOR RESEARCH / BORROW DESIGN · **Expected gain**: MEDIUM · **Priority**: P3

### H-065 SQLite (already a corpus target; amalagmated C reference)
- **TYPE**: LIBRARY · **Source**: sqlite.org (fossil repo) · **License**: Public Domain · **Language**: C
- **Category**: 60 utilities, 43 serialization
- **What it does**: The database engine Android ships (`SQLiteDatabase` shadows).
- **Why useful**: Our storage lane (test_file_sandbox/shared_prefs + exp085_phase10_sqlite evidence) eventually wants real SQLite semantics; the amalgamation is drop-in C.
- **Potential reuse**: USE DIRECTLY · **Expected gain**: MEDIUM (storage lane) · **Priority**: P1

### H-066 DrMemory / SQLite fuzz corpus / oss-fuzz integration notes
- **TYPE**: RESEARCH PROJECT · **Source**: github.com/dynamorio/drmemory (LGPL); google.github.io/oss-fuzz · **License**: LGPL-2.1/Apache-2.0
- **Category**: 27 fuzzing, 37 memory analysis
- **What it does**: Alternative memory debugger + the OSS-Fuzz playbook for long-running fuzz infra.
- **Why useful**: If the project ever moves to OSS-Fuzz, the harnesses built for H-036 plug straight in.
- **Potential reuse**: USE FOR RESEARCH · **Expected gain**: LOW-MEDIUM · **Priority**: P3

---

## Part IX — Priority summary & self-review record (PHASE 9)

### Counts

| Priority | Entries |
|---|---|
| P0 (directly useful now) | 13 — H-001 H-002 H-003 H-004 H-005 H-006 H-013 H-018 H-019 H-023 H-036 H-046 H-052 |
| P1 (likely useful soon) | 23 — H-007 H-008 H-010 H-011 H-014 H-017 H-020 H-021 H-026 H-031 H-032 H-037 H-038 H-039 H-042 H-044 H-048 H-054 H-055 H-057 H-059 H-060 H-065 |
| P2 (useful later) | 26 — H-009 H-012 H-015 H-016 H-022 H-024 H-025 H-027 H-028 H-029 H-030 H-033 H-034 H-035 H-040 H-041 H-043 H-045 H-047 H-049 H-050 H-053 H-056 H-061 H-062 H-063 |
| P3 (reference only) | 4 — H-051 H-058 H-064 H-066 |
| **Total** | **66 (13+23+26+4)** |

### PHASE 9 self-review decisions (this list was critically reviewed, not just copied)

- **Merged**: dex2jar+enjarify → one entry (H-011, same oracle role); Anbox→Waydroid (H-032, one maintained lineage); lottie-android+lottie-web → one entry (H-028); radare2+rizin (H-051); Valgrind kept separate from ASan (complementary, not duplicate); AFL++ merged into libFuzzer entry (H-036, same role two engines).
- **Demoted to P3**: radare2 (Ghidra covers the need better for us); protobuf/flatbuffers (no current parser lane); Dolphin/RPCS3 (culture, not code); DrMemory (ASan+Valgrind cover it); miniz (zlib already integrated; malformed-ZIP role kept at P2).
- **Promoted** (missing from most naive lists): Robolectric (H-019) — the single closest philosophical sibling; Apache-Harmony-inside-libcore (H-002) — the exact law source for our bridges; CTS (H-044) as fixture mine; F-Droid version pinning (H-052) as the structural fix for the K-26 corpus-loss class; Frida (H-042) as the ART ground-truth bridge; ASan/UBSan (H-046) as the free deep bug-hunt; API-mining catalogs (H-057) to automate the gap matrix.
- **Rejected (with evidence)**: closure-compiler (JVM-optimizer, no DEX relevance), Genymotion (proprietary), APKMirror (not open-source; corpus must stay legally clean), Rosetta/box86 (CPU-level translation out of scope — our bytecode is Dalvik, not machine code), Ionic/Capacitor (app frameworks, not runtime compatibility).
- **TYPE/USE discipline**: every entry carries an explicit TYPE (TOOL/LIBRARY/REFERENCE IMPLEMENTATION/CORPUS/TEST FRAMEWORK/DEBUGGING TOOL/RESEARCH PROJECT) and a USE verdict (USE DIRECTLY / PORT / BORROW DESIGN / USE AS ORACLE / USE FOR TESTING / USE FOR RESEARCH).

### Category coverage map (task's 60 categories)

| # | Category | Entries |
|---|---|---|
| 1 | Android Runtime | H-001, H-002 |
| 2 | Dalvik / DEX | H-001, H-003, H-005, H-006, H-007, H-011, H-012 |
| 3 | ART | H-001, H-032 |
| 4 | APK / AAB | H-004, H-005, H-013, H-017, H-058 |
| 5 | AXML | H-004, H-013 |
| 6 | ARSC / Resources | H-004, H-013 |
| 7 | Android Framework | H-002, H-014, H-018, H-019, H-020, H-044, H-056, H-057 |
| 8 | Android UI | H-018, H-019, H-020, H-043 |
| 9 | Rendering | H-023, H-024, H-025, H-026, H-029, H-030, H-041 |
| 10 | Skia | H-023 |
| 11 | OpenGL / GLES | H-030 |
| 12 | Vulkan | H-030 |
| 13 | Image decoding | H-023, H-027, H-029 |
| 14 | SVG | H-026, H-027 |
| 15 | Animation | H-028 |
| 16 | rlottie | H-028 (rlottie itself: integrated, §0) |
| 17 | Emulator | H-032, H-033, H-034, H-064 |
| 18 | Headless Android | H-032, H-033 |
| 19 | Linux Android compatibility | H-031, H-032, H-033 |
| 20 | Java runtime | H-002, H-021, H-055 |
| 21 | JVM | H-007, H-008, H-055 |
| 22 | JNI | H-056 |
| 23 | bytecode | H-001, H-003, H-011, H-012 |
| 24 | reverse engineering | H-005, H-006, H-011, H-050 |
| 25 | disassembly | H-017, H-050, H-051 |
| 26 | binary analysis | H-017, H-050, H-051 |
| 27 | fuzzing | H-036, H-066 |
| 28 | differential testing | H-011, H-038, H-042, H-045, H-055 |
| 29 | property testing | H-038, H-039 |
| 30 | screenshot testing | H-040, H-041 |
| 31 | visual regression | H-040, H-041 |
| 32 | UI automation | H-043 |
| 33 | input simulation | H-043 |
| 34 | debugging | H-042, H-046, H-047 |
| 35 | tracing | H-042, H-047, H-048 |
| 36 | profiling | H-048, H-049 |
| 37 | memory analysis | H-046, H-047, H-049, H-066 |
| 38 | APK corpus mining | H-005, H-006, H-039, H-052, H-053, H-054 |
| 39 | API mining | H-057 |
| 40 | resource mining | H-057, H-004 |
| 41 | compiler technology | H-009 |
| 42 | interpreter technology | H-001, H-007, H-008, H-009, H-010, H-034, H-064 |
| 43 | serialization | H-058, H-065 |
| 44 | XML | H-014, H-015 |
| 45 | ZIP/APK infrastructure | H-004, H-016 |
| 46 | font/text | H-021, H-022 (FreeType/HarfBuzz/FriBidi: integrated §0) |
| 47 | networking compatibility | H-063 |
| 48 | crypto compatibility | H-062 |
| 49 | threading/concurrency | H-002 (java.util.concurrent laws via libcore), H-019 (Handler/Looper shadow laws) |
| 50 | process/runtime isolation | H-031, H-035 |
| 51 | sandboxing | H-035 |
| 52 | CI | H-060, H-059 |
| 53 | GitHub Actions | H-060 |
| 54 | reproducible builds | H-045, H-061 |
| 55 | test harnesses | H-003, H-019, H-036, H-037, H-044 |
| 56 | corpus management | H-037, H-052, H-053 |
| 57 | differential oracle | H-032, H-042, H-044 |
| 58 | fuzz corpus | H-036, H-053 |
| 59 | Android compatibility projects | H-031, H-032, H-052 |
| 60 | small useful utilities | H-054, H-059, H-065 |

---

## SESSION STATUS — 2026-09-04 (live update: used / inspected / evidence)

This section makes the list a LIVING record: per-entry real status from the
2026-09-04 autonomous engineering session, with evidence. Status vocabulary:
CANDIDATE → INSPECTED → REUSABLE → ADAPTED → INTEGRATED.

### S-1. INTEGRATED this session (code + evidence in-repo)

| What | Upstream | License | Integration point | Evidence |
|---|---|---|---|---|
| Windows x64 toolchain | llvm-mingw 20260826 (mstorsjo/llvm-mingw) | Apache-2.0/LLVM + mingw-w64 | `miniandroid/scripts/build_windows.sh` | MiniAndroid.exe PE32+ 5,011,968 B; wine smoke: simplestopwatch `2a12587a` byte-identical to Linux golden |
| zlib 1.3.1 / libpng 1.6.44 / libjpeg **IJG 9f** / freetype 2.13.3 / harfbuzz 8.5.0 / fribidi 1.0.16 / libwebp 1.4.0 (Windows ports) | official upstream repos | zlib/PNG/IJG/FTL/MIT/LGPL/BSD | static-linked into the .exe by the build script | full clean-room rebuild reproduced; exe renders golden-identical |
| fribidi bidi tables | fribidi `gen.tab` + Unicode UCD **16.0.0** (unicode.org) | LGPL-2.1+ / UCD license | generated 7 `.tab.i` tables in-script (bidi-type/joining/arabic-shaping/mirroring/brackets×2) | reproducible generation inside `build_windows.sh` |
| Wine-based Windows smoke harness | Debian wine 10.0 / Kron4ek Wine-Builds | LGPL-2.1 | external harness (not committed yet) | exe runs, `version` + `run` commands OK; screenshot SHA equal to Linux |

Codec availability model added to the runtime itself: `MINIANDROID_HAVE_WEBP`
/ `MINIANDROID_HAVE_LOTTIE` compile guards (mirrors AOSP codec availability);
disabled codecs return an EXPLICIT capability error — never fake success.
Lottie (rlottie) stays Linux-host-build-only for now (needs cmake; guarded off
on Windows v1 — honestly reported).

### S-2. INSPECTED this session (source opened, APIs mapped — not yet adapted)

| Entry | Inspected surface | Verdict for MiniAndroid |
|---|---|---|
| **auxten/libarsc** | `jni/libarsc/arsc.cpp` (1,838 lines) — vendored AOSP `ResTable`: Header/Type/Package/PackageGroup structs, `ResTable::add/getEntry/resolve` | REUSABLE as ORACLE. KEY FINDING: our `res_config.cpp` **already mirrors AOSP verbatim** (`match()` @2909, `isBetterThan()` @2641, `isLocaleBetterThan()` @2520 — with line refs in comments; `arsc_parser.cpp` selects buckets via `match`+`isBetterThan` — see arsc_parser.cpp:480-494). The remaining upstream gap is narrower than assumed: PackageGroup resolution + bag/complex values + dynamic references. |
| **johnsonlee/aapt** (sdklite) | `ChunkParser.java`, `StringPool.java` (212), `ResourceTable.java` (1,209) + visitors, `getResourceName(resId)` | REUSABLE as ORACLE for chunk grammar + resource-name resolution. Clean, small, readable. Best use: differential tests for our `arsc_parser` (id → name → config → value) rather than a port. |

### S-3. STATUS table updates (existing entries)

| ID | Old status | New status | Note |
|---|---|---|---|
| H-001 (AOSP ART) | P0 oracle | ORACLE-USED (ongoing) | fill-array-data + aput bounds semantics commits (2a99862, 63b0aa3) came from this oracle; compose chain traced against AOSP View/ViewGroup/ViewRootImpl laws |
| H-00x Resource/ARSC family | candidate | PARTIALLY ALIGNED (see S-2) | config selection already AOSP-verbatim; package-group/bag gaps remain |
| FreeType/HarfBuzz/FriBidi/libpng/libjpeg/libwebp/zlib | integrated (Linux) | INTEGRATED (Linux + **Windows**) | this session |
| rlottie | integrated (Linux) | INTEGRATED + OPTIONALIZED | `MINIANDROID_HAVE_LOTTIE=0` for Windows v1; explicit error, no fake |

### S-4. NEW entries proposed by this session

| ID | Source | License | TYPE/USE | Priority | Why |
|---|---|---|---|---|---|
| H-070 | **Kron4ek/Wine-Builds** (self-contained wine tarballs) + Debian `wine`/`wine64`/`libwine` .deb extraction | LGPL-2.1 | TOOL · USE FOR TESTING | P1 | Real Windows-binary smoke testing from Linux CI (no root needed with .deb extraction + LD_PRELOAD path remap); validated this session |
| H-071 | **mstorsjo/llvm-mingw** | Apache-2.0 | TOOLCHAIN · USE DIRECTLY | P0 | The working Linux-hosted Windows cross toolchain for this repo (clang 23.1 + mingw-w64 ucrt); validated end-to-end |
| H-072 | **AOSP RenderNode / RecordingCanvas** (`platform_frameworks_base` graphics) | Apache-2.0 | REFERENCE · PORT NEXT | P0 | Compose 1.7 routes ALL composed drawing through RenderNode.beginRecording→RecordingCanvas→drawRenderNode — our CanvasShadow sees 0 ops today. Bridging these is THE next Compose frontier (dooz content rendering). |
| H-073 | **skylot/jadx** | Apache-2.0 | TOOL · USE AS ORACLE | P0 (workflow) | mandated as the engineering oracle for real-APK call chains (decompile → expected semantics → MiniAndroid execution diff); not yet used this session — adopt in the RenderNode cycle |

### S-5. Session headline (context for statuses above)

- Windows: REAL MiniAndroid.exe produced and cross-verified (byte-identical
  golden vs Linux on wine).
- Compose: **composition boundary crossed** — ComposeView children 0 → 1
  (AndroidComposeView materializes; onAttachedToWindow dispatches on both).
  Before this session this was documented as permanently blocked (K-24).
- Golden safety: 12-app corpus without gate → 11/12 byte-identical; dooz's
  documented blank (31ddd4d5) became the honest §17 placeholder (e33e6e75).
