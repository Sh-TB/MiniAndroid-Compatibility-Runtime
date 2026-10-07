# CONT-11 Task 2 — External DEX/JVM Runtime Research (bounded feasibility survey)

Task ID: 2-external-runtime-research
Date: 2026-10-07
Method: web search + direct source inspection. Repositories actually cloned and read: `A2OH/dalvik-universal`, `A2OH/westlake`, `celymyst/Mihon-Runner`. AOSP ART source fetched file-by-file from android.googlesource.com (test.py, build/Android.bp, libartpalette headers, runtime.h, test/001-HelloWorld). GitHub REST search API used for repo metadata (core API was rate-limited; search API still had quota). Robolectric/kotlinx.coroutines/Avian READMEs fetched raw.

---

## 1. Executive summary

1. **No existing open-source project executes real Compose APKs on a desktop host without Android OS.** The closest proven prior art embeds the Android framework as a guest runtime next to a real VM — exactly MiniAndroid's MODE B — but only on OpenHarmony (Westlake) and only for View-based apps.
2. **The strongest prior art found is A2OH/westlake + A2OH/dalvik-universal** (Apache-2.0, active 2026): a 64-bit port of KitKat Dalvik running DEX on x86_64 Linux *without Android*, plus a 2,056-class shim layer that ran a real 177 MB Play Store APK (119,275 classes, Dagger/Hilt, Firebase, Kotlin coroutines) on a phone. Views + lifecycle + coroutines: yes. Compose: no.
3. **AOSP ART is genuinely host-executable** (first-class `--host` test mode, PAL abstraction = 21 OS methods, `-hostdex` boot jars). It executes DEX/Kotlin/coroutines on x86_64 without Android — but ships **zero** `android.*` framework classes, so real APKs die at the first framework call. ART host + a Westlake-style shim classpath is the theoretically cleanest MODE B (kills all DEX-version risk), at high integration cost.
4. **kotlinx.coroutines does not need to be "ported"**: the real library is already inside the APK's DEX (dooz carries 1.9.0). A correct DEX VM executes it verbatim; the host must only supply correct primitives (atomic CAS fields, executor/delay scheduling, `Dispatchers.Main` → Handler/Looper/Choreographer bridge). Its source (Apache-2.0) is a legitimate semantic oracle.
5. DEX interpreters on GitHub beyond Dalvik/ART are educational toys (Rust 576-line, Java 3-opcode, Racket abstract). Decompilers (droidsaw, jadx) and VM managers (DroidVM, Skydnir) are categorically not runtimes — verified from source/descriptions.
6. The three named mystery candidates all exist and were verified: **DroidVM** = VM manager on Android phones (irrelevant), **droidsaw** = Rust decompiler/audit suite (reference-only, ships Lean-4-verified AXML parsing), **AndroidRecomp** = native ARMv7→x86 game recompiler (wrong problem). **Skydnir** = Docker-Engine-API manager on Android (irrelevant).

---

## 2. Per-candidate records

### CANDIDATE: AOSP ART (host build: test.py, dalvikvm, libartpalette)
SOURCE: https://android.googlesource.com/platform/art/ (fetched: `test.py`, `build/Android.bp`, `libartpalette/include/palette/palette_method_list.h`, `runtime/runtime.h`, `test/001-HelloWorld`)
WHAT IT ACTUALLY EXECUTES (source evidence):
- `test.py` exposes `--host` as a first-class mode ("test-art-host-run-test-...-001-HelloWorld32"); run-tests execute real DEX against a host `dalvikvm`.
- `build/Android.bp` builds `-hostdex` boot jars specifically "to test ART on host" (`conscrypt-hostdex`, `core-icu4j-hostdex`, plus core-oj/core-libart family). Boot classpath = java.*/javax.* core libs ONLY.
- `libartpalette/palette_method_list.h` = the entire OS contract: 21 methods (sched priorities, tracing, ashmem region create/protect, dex2oat notifications, JNI invocation notifications, lock contention, task profiles).
- No `android.*` framework anywhere in the ART tree; no Looper/Choreographer/View/Canvas.
DEX? YES — full modern DEX incl. DEX-038/039 opcodes (invoke-custom, invoke-polymorphic) in interpreter.
JVM? No (DEX machine, though libcore is OpenJDK-derived).
KOTLIN? YES for Kotlin-generated DEX (language + stdlib semantics via classpath).
COROUTINES? YES (they are plain DEX + atomic intrinsics; ART interpreter runs them — ART's own tests use suspend).
ANDROID FRAMEWORK? NO — zero android.* classes (only `dalvik.system`).
COMPOSE? NO.
GRAPHICS? NO.
x86/x86_64 HOST CPU? YES (host tests run x86_64 by default).
LICENSE: Apache-2.0.
BUILD COST: high (~700K+ LOC C++; but Google builds it for host out of the box with soong; interpreter-only trim possible).
INTEGRATION COST: high — needs PAL host impl (small, ~21 mostly-no-op methods), ANDROID_ROOT/ANDROID_DATA layout, boot image, and then EVERYTHING in section 3 (framework layers) supplied by MiniAndroid.
CLASSIFICATION: EXECUTION-CAPABLE (DEX/Kotlin/coroutines on host proven in-tree) — but for real APKs: PARTIAL (no android.* framework).
ONE-LINE JUSTIFICATION: ART host already proves "real VM executes real DEX on Linux without Android kernel"; the missing half is exactly MiniAndroid's framework bridge.

### CANDIDATE: A2OH/dalvik-universal
SOURCE: https://github.com/A2OH/dalvik-universal (cloned @ c24b020880c3e522b6aabf317cc1c4bf13d52407 "Dalvik VM 64-bit port: x86_64 + OHOS ARM32/ARM64")
WHAT IT ACTUALLY EXECUTES (source evidence):
- KitKat Dalvik portable interpreter (vm/Interp.cpp, mark-sweep GC) ported to 64-bit: `dreg_t` (=uintptr_t) in 5 core files; 46 documented 64-bit fixes (register width, JNI bridges, IndirectRefTable, atomics, HeapBitmap).
- libdex/DexFile.h adds `DEX_MAGIC_VERS_038` "structurally compatible, just newer version tag"; grep shows **no invoke-custom/invoke-polymorphic handling** — DEX-038-only opcodes would fail.
- `libcore_bridge.cpp` (1,658 lines, 30+ JNI natives: Math, ICU, Regex, I/O, System) + boot classpath ~4,000 java.* classes (`core-android-x86.jar`).
- Runs with `-Xverify:none -Xdexopt:none` on x86_64 Linux; README claims tests: 14/14 "MockDonalds" (Activity lifecycle, Intent, Bundle, View tree, rendering), 2,416 headless shim tests, "Real APK pipeline: 3 pass (APK unzip, manifest parse, Activity launch)".
DEX? YES (DEX 035 executable; 038 version-tag accepted, 038-only opcodes NOT implemented).
JVM? No.
KOTLIN? Partially — Kotlin DEX executes, but modern Kotlin/R8 output using invoke-custom/string-concat invokedynamic/lambdas-via-metafactory is at risk on a KitKat interpreter.
COROUTINES? Possible in principle (plain DEX) but untested/unclaimed; `Dispatchers.Main` needs android.os Looper shim.
ANDROID FRAMEWORK? Partial — outside this repo, in Westlake: KitKat `android.view.View` (30,424 lines) etc. as unmodified AOSP code with 134 dependency stubs.
COMPOSE? NO (KitKat-era framework; no androidx runtime provided by them).
GRAPHICS? Yes, software rendering of View tree claimed (test-verified); no HWUI/Skia.
x86/x86_64 HOST CPU? YES (native Linux x86_64 `build/dalvikvm`).
LICENSE: Apache-2.0 (AOSP lineage: MODULE_LICENSE_APACHE2 + NOTICE; README badge Apache-2.0).
BUILD COST: low (plain C++/make, no soong).
INTEGRATION COST: medium — embed VM, replace their libcore_bridge with MiniAndroid primitives, map guest objects ↔ MiniAndroid services; DEX-version risk is the hidden tax.
CLASSIFICATION: EXECUTION-CAPABLE (for DEX-035-era + tolerant-038 code on x86_64 host, demonstrably, without Android OS).
ONE-LINE JUSTIFICATION: The only open-source VM besides ART demonstrably running DEX on a bare x86_64 host with real-APK plumbing tests — but it is KitKat-obsolete and unverified on modern R8 bytecode.

### CANDIDATE: A2OH/westlake
SOURCE: https://github.com/A2OH/westlake (cloned @ 545e3c6f6f918c54796d701d09bf6ebd7f5700df, Sep 2026, active; docs/engine/ARCHITECTURE.md read)
WHAT IT ACTUALLY EXECUTES (source evidence from README + ARCHITECTURE.md + tree):
- "Runs unmodified Android APKs on OpenHarmony" by embedding the Android framework as a guest runtime over Dalvik/ART boot images: 2,479 java shim files (README: 2,056 shim classes), 193K lines of *unmodified* AOSP framework code (166 files), ~25 C bridge functions + 1 host Activity, ~15 HAL-level boundaries.
- Proven target (2026-03-30 status): McDonald's Play Store APK (177 MB, 119,275 classes, 33 DEX files, Dagger/Hilt, Firebase, GMS, **Kotlin coroutines**) — full DI graph, performCreate→Start→Resume through AppCompat/Fragment/Hilt, splash rendered via DLST display-list frames piped to host SurfaceView with Skia replay.
- ARM64 dalvikvm 16 MB static binary with JIT, on musl libc (not bionic). Native stubs: Inflater/Deflater (zlib), ICU regex, JarFile, 20 Character methods, 10 Typeface methods. GMS/Firebase stubs.
- Their API-coverage analysis: of 57,000 Android APIs, "94% of the unmapped API gap is handled automatically by the engine runtime. Only 6% needs real platform bridge work" — i.e., the framework is self-contained Java; host coupling is ~15 boundaries (surface, input, services).
- Compose: only `shim/java/androidx/compose/ui/R.java` exists (a resource class) — **no Compose runtime support**.
DEX? YES (real APK DEX, real VM).
JVM? No.
KOTLIN? YES (Kotlin APK code executes; coroutines named as running).
COROUTINES? YES (same evidence).
ANDROID FRAMEWORK? YES — View/TextView/ImageView/RecyclerView, Activity lifecycle, LayoutInflater, binary AXML + resources.arsc, AppCompat/Fragment/Hilt chains; NOT Compose/HWUI.
COMPOSE? NO.
GRAPHICS? YES (DLST → Skia replay to host surface; view-level).
x86/x86_64 HOST CPU? NO — ARM64/ARM32 on OpenHarmony (x86_64 only via their dalvik-universal sibling, Linux tests).
LICENSE: Apache-2.0.
BUILD COST: n/a (exists).
INTEGRATION COST: as prior art — low for design reuse (architecture is directly MiniAndroid's MODE B); their shim corpus is Apache-2.0 Java and portable to a host VM.
CLASSIFICATION: EXECUTION-CAPABLE (real APKs incl. Kotlin + coroutines + View UI on a non-Android host OS — the direct precedent for MODE B).
ONE-LINE JUSTIFICATION: The only open-source project that demonstrably runs a real modern Play Store APK's Kotlin/coroutine/DI code on a non-Android OS with a small (~25 C functions) host bridge — Views, not Compose.

### CANDIDATE: notmyst33d/dalvik (Rust)
SOURCE: https://github.com/notmyst33d/dalvik (README fetched)
WHAT IT ACTUALLY EXECUTES: DEX parser complete (dalvikdex); instruction decoder 3 opcodes tested (const-string, invoke-virtual, return); `dalvikvm` module: "Bytecode interpretation" and "Standard library" checkboxes UNCHECKED.
DEX? parser yes / runtime no. JVM? No. KOTLIN? No. COROUTINES? No. ANDROID FRAMEWORK? No. COMPOSE? No. GRAPHICS? No. x86/x86_64 HOST? It would be host-side Rust, but no execution exists.
LICENSE: none (unlicensed!). BUILD COST: n/a. INTEGRATION COST: n/a.
CLASSIFICATION: ANALYSIS-ONLY.
ONE-LINE JUSTIFICATION: A WIP DEX parser; per the classification rules a DEX parser is not a DEX runtime.

### CANDIDATE: vimalloc/dexterpreter (Java)
SOURCE: https://github.com/vimalloc/dexterpreter (7 stars, Java, no license)
WHAT IT ACTUALLY EXECUTES: educational Dalvik bytecode interpreter in Java (runs trivial DEX methods inside a JVM).
DEX? toy yes. JVM? runs on JVM. KOTLIN? No. COROUTINES? No. ANDROID FRAMEWORK? No. COMPOSE? No. GRAPHICS? No. x86 HOST? via JVM only.
LICENSE: none found. BUILD COST: n/a. INTEGRATION COST: n/a.
CLASSIFICATION: ANALYSIS-ONLY.

### CANDIDATE: celymyst/Mihon-Runner (Rust)
SOURCE: https://github.com/celymyst/Mihon-Runner (tarball inspected: src/interpreter/interpreter.rs = 576 lines)
WHAT IT ACTUALLY EXECUTES: a DEX parser + minimal interpreter whose `main.rs` hardcodes calling `getUserAgent`/`getName`/`isCorrectUserAgent` on Mihon extension classes with hardcoded native stubs (println). It is a bespoke plugin runner for Mihon (Kotlin-built) extension APKs.
DEX? yes, micro-scope. JVM? No. KOTLIN? yes — runs Kotlin-built plugin DEX (tiny surface). COROUTINES? No. ANDROID FRAMEWORK? No (extension API only). COMPOSE? No. GRAPHICS? No. x86/x86_64 HOST? YES (host Rust).
LICENSE: none found. BUILD COST: low. INTEGRATION COST: n/a.
CLASSIFICATION: ANALYSIS-ONLY (borderline PARTIAL for its niche).
ONE-LINE JUSTIFICATION: Demonstrates "Kotlin-built DEX executing on a host interpreter" exists in toy form, nothing more.

### CANDIDATE: philomates/dalvik-abstract-interpreter (Racket)
SOURCE: GitHub search result (10 stars) — "Abstract Interpreter for Dalvik bytecode".
CLASSIFICATION: ANALYSIS-ONLY (static analysis, not concrete execution; per rule "decompiler != interpreter" and analysis != runtime).

### CANDIDATE: ParanoidAndroid/android_dalvik
SOURCE: GitHub search result (6 stars, Assembly) — "Dalvik java interpreter" (AOSP Dalvik fork for a custom ROM).
CLASSIFICATION: REFERENCE-ONLY (Dalvik source fork; nothing beyond AOSP).

### CANDIDATE: droidsaw/droidsaw (Rust suite)
SOURCE: https://github.com/droidsaw/droidsaw (32 stars, BSD-3-Clause) + sub-crates droidsaw-dex ("Parses, builds CFG, SSA via Braun, emits Java"), droidsaw-apk (APK/AAB/XAPK parser + signing v1–v4 audit), droidsaw-hermes, droidsaw-dart, droidsaw-il2cpp, droidsaw-lean (Lean 4 verification harness, "20 theorems, no sorry" incl. AXML parsing).
WHAT IT ACTUALLY EXECUTES: nothing — decompilation/audit only.
CLASSIFICATION: REFERENCE-ONLY (droidsaw-lean's machine-checked AXML/DEX theorems are a usable semantic oracle for MiniAndroid's parser work).

### CANDIDATE: Droid-VM/DroidVM (838 stars, Java, GPL-3.0)
SOURCE: GitHub search — "Run virtual machine on Android Phones" (VM manager for Android; prebuilt-images repo + installer).
CLASSIFICATION: IRRELEVANT (VM manager ≠ Kotlin runtime — the rule literally named for this).

### CANDIDATE: ryo100794/skydnir (1 star, Python, NOASSERTION license)
SOURCE: https://github.com/ryo100794/skydnir (README fetched) — Docker-Engine-API-compatible runtime-cell manager running ON Android (terminals, rootfs layers, dev templates). "no-PRoot Android direct executor" refers to running Linux binaries on the phone, not DEX.
CLASSIFICATION: IRRELEVANT.

### CANDIDATE: jessicanataliagta/AndroidRecomp (+ sp00nznet/androidrecomp, BackStabRecomp)
SOURCE: GitHub search — "profile-driven ARMv7 Android-to-Windows compatibility runtime for native games" (Python, MIT); sp00nznet fork: "Statically recompile Android games' native ARM64 engines into native desktop applications. Loader, Bionic/Android shim".
CLASSIFICATION: REJECTED (native ARM recompiler ≠ x86/x86_64 Kotlin execution — the rule named for this). Relevant only if MiniAndroid ever needs native .so game engines.

### CANDIDATE: Robolectric
SOURCE: https://github.com/robolectric/robolectric (README fetched; developer.android.com + Robolectric 4.10+ release notes confirm RNG)
WHAT IT ACTUALLY EXECUTES: Android app/test code inside a plain JVM: real android-all framework jars (AOSP framework compiled for JVM, API 23–37), Robolectric Native Graphics (RNG) = real Skia native code rendering on host since 4.10, "Robolectric can also run UI tests such as Espresso or **Compose** tests" (developer.android.com), screenshot testing via Roborazzi, interactive simulator since 4.15.
DEX? NO — it runs JVM bytecode (Gradle builds classes, never loads APK DEX). JVM? YES. KOTLIN? YES (compiled JVM classes). COROUTINES? YES (JVM). ANDROID FRAMEWORK? YES — the real AOSP framework classes + a large simulation/shim layer. COMPOSE? YES — Compose UI tests render on JVM via RNG. GRAPHICS? YES (Skia). x86/x86_64 HOST? YES.
LICENSE: Apache-2.0 (robolectric + android-all preinstrumented jars).
BUILD COST: n/a. INTEGRATION COST: not an APK runtime — requires source-build pipeline; could serve as a giant *semantic oracle* for framework behavior on host.
CLASSIFICATION: EXECUTION-CAPABLE for the JVM path (Kotlin+coroutines+Compose+real framework classes on host JVM), REFERENCE-ONLY as an APK runtime.
ONE-LINE JUSTIFICATION: The strongest proof that "Compose + real framework + Skia on a host JVM" works at scale — but it converts the problem to JVM bytecode and cannot consume APKs.

### CANDIDATE: Host JVM + dex2jar / enjarify (conversion path)
SOURCE: https://github.com/pxb1988/dex2jar (13,142 stars, Apache-2.0), https://github.com/google/enjarify (2,744 stars, Apache-2.0)
WHAT IT ACTUALLY EXECUTES: nothing itself; converts DEX→JVM class files. Known conversion path weaknesses: lossy mapping (registers→stack), incomplete DEX coverage, R8/obfuscator constructs, invokedynamic/coroutine metadata handled imperfectly; and after conversion the app still has no android.* classes.
CLASSIFICATION: REFERENCE-ONLY (converter ≠ runtime; identity broken by rule).
ONE-LINE JUSTIFICATION: Usable for analysis or a Robolectric-style source-built pipeline; not a faithful APK execution path.

### CANDIDATE: TeaVM
SOURCE: https://github.com/konsoletyper/teavm (3,121 stars, Apache-2.0) — "Compiles Java bytecode to JavaScript, WebAssembly and C".
WHAT IT ACTUALLY EXECUTES: JVM bytecode (AOT-compiled to WASM/C) with its own runtime; used for LibGDX browser ports.
CLASSIFICATION: PARTIAL (exotic MODE-B substrate: dex2jar→TeaVM-C would execute app logic on host; same conversion/identity breakage as dex2jar + no android.*).
ONE-LINE JUSTIFICATION: A real JVM-semantics execution engine in open source, but it consumes class files, not DEX, and brings its own runtime.

### CANDIDATE: Avian JVM
SOURCE: https://github.com/ReadyTalk/avian (README fetched)
WHAT IT ACTUALLY EXECUTES: JVM bytecode on Linux x86_64/ARM/iOS/etc. with its own subset class library or OpenJDK classpath; README: "not currently being developed, maintained, or supported".
CLASSIFICATION: PARTIAL (would execute converted bytecode; unmaintained; no Android framework).

### CANDIDATE: JamVM (+ libretro-JamVM/freej2me ecosystem)
SOURCE: GitHub mirrors (cfriedt/jamvm, jserv/jamvm "JamVM 2 + OpenJDK", libretro/libretro-JamVM), upstream on SourceForge.
WHAT IT ACTUALLY EXECUTES: JVM bytecode, small C interpreter (~50-60K LOC), pairs with OpenJDK or GNU Classpath; libretro port used with freej2me to run J2ME MIDlets on desktops.
CLASSIFICATION: PARTIAL (proven embedding of a small JVM into a non-JVM host app; no DEX, no Android; GPL-2.0 + Classpath exception — GPL tax for MiniAndroid).
ONE-LINE JUSTIFICATION: Architectural precedent for "embed small VM + bridge to host UI" (the freej2me/libretro model), wrong bytecode family.

### CANDIDATE: KiVM and other C++ toy JVMs (Purpuri, TinyJ, CoconutJVM, core-vm, jankvm)
SOURCE: GitHub search "jvm interpreter language:c++" (KiVM 258 stars, MIT, "only Java 8", "Inspired by Hotspot In Action"; rest ≤14 stars).
CLASSIFICATION: ANALYSIS-ONLY (educational; no class libraries beyond basics).

### CANDIDATE: kotlinx.coroutines (library as oracle / as in-APK code)
SOURCE: https://github.com/Kotlin/kotlinx.coroutines (master; JobSupport.kt, HandlerDispatcher.kt fetched)
WHAT IT ACTUALLY EXECUTES / DEPENDS ON (source evidence):
- `JobSupport.kt` imports `kotlinx.atomicfu.*` — atomic fields are compile-time transformed (JVM: volatile + VarHandle/sun.misc.Unsafe CAS; native/JS: runtime-provided).
- JVM scheduling: java.util.concurrent (ScheduledThreadPoolExecutor for `delay`/Default), FJP/threads; `Dispatchers.Main` (kotlinx-coroutines-android) = `Handler(Looper.getMainLooper())` + Choreographer for frame alignment — i.e., **android.os.Looper/Handler/Choreographer are hard dependencies of the Android Main dispatcher**.
- The suspend machinery (state machines, BaseContinuationImpl, intrinsics) is compiler-generated DEX + kotlin-stdlib classes — no JVM-only magic.
- dooz (MiniAndroid corpus) already ships kotlinx-coroutines 1.9.0 with atomicfu-transformed `$volatile` fields (worklog CONT-10).
LICENSE: Apache-2.0.
CLASSIFICATION: REFERENCE-ONLY as a project — but as in-APK code it is EXECUTED verbatim by any correct DEX runtime; MiniAndroid's job is the primitives, not the library.
ONE-LINE JUSTIFICATION: Executing the actual library in a non-JVM host is feasible and already happens on MiniAndroid; the semantic-oracle use is legitimate and license-clean.

### CANDIDATE: kotlin-stdlib
SOURCE: https://github.com/JetBrains/kotlin (Apache-2.0).
WHAT IT IS: JVM (+multiplatform) actualizations of the stdlib; per-library sources are the law for collections/sequences/contracts; license permits derivation.
CLASSIFICATION: REFERENCE-ONLY (semantic oracle; not an execution engine; DEX≠JVM bytecode so it cannot "run" guest DEX objects — object identity would not survive a JVM hop without conversion, which is broken by rule).

### CANDIDATE: Anbox / Waydroid / redroid / ARC++ / Android-x86 / Cuttlefish / Celadon
SOURCE: LWN "Android apps on Linux with Waydroid" (search snippet), redroid GitHub ("Android in Cloud", multi-arch container), AOSP/Chromium.
WHAT THEY ACTUALLY EXECUTE: complete Android OS images (kernel modules binder/ashmem, system_server, SurfaceFlinger) in containers/VMs; apps run inside a full Android.
CLASSIFICATION: REJECTED for MiniAndroid's mission ("without Android OS" is the premise); noted as prior-art family + API-reference source.
ONE-LINE JUSTIFICATION: They prove app compatibility by shipping the whole OS — the exact thing MiniAndroid exists to avoid.

### CANDIDATE: Alien Dalvik (Myriad Group)
SOURCE: OSNews 2011 + Sailfish forum (search snippets) — "Android App Support" on Sailfish is the commercial Alien Dalvik.
CLASSIFICATION: REJECTED (proprietary, closed; no source evidence available).

### CANDIDATE: unidbg (mentioned for completeness, native-libs category)
SOURCE: https://github.com/zhkl0228/unidbg — emulates Android native libraries (ARM) on host JVM via unicorn with bionic/syscall shims.
CLASSIFICATION: REJECTED for DEX/Kotlin (it executes native ARM code, not bytecode) — but a mature reference for bionic/JNI-shim design.

---

## 3. The missing-layers analysis for ART reuse (exact list)

ART on host executes DEX; to run a real APK the following layers must be supplied (none exist in platform/art):

1. **android.* boot-classpath framework classes** (framework.jar): android.view, android.graphics, android.os (Handler/Looper/MessageQueue/Choreographer), android.content (Context/Resources/AssetManager/Intent/Binder), android.text, android.util, android.app, android.net, android.provider... ≈4,000 public API classes; framework.jar ships ~25K classes total. ART ships none of them.
2. **framework-res.apk / android.content.res native bridge** (libandroidfw.so: AssetManager2, ResTable, TypedValue, AXML parsing).
3. **system_server services**: ActivityManagerService (lifecycle, intents, back stack), PackageManagerService (manifest parse, permissions), WindowManagerService (windows, input focus), plus Notification/Vibrator/Alarm/JobScheduler surfaces. Westlake replaces these with an in-process MiniServer + MiniActivityManager.
4. **Binder IPC** (libbinder + /dev/binder or in-process replacement) — framework code calls services through Binder proxies.
5. **libandroid_runtime.so**: AndroidRuntime::start + ~200 framework JNI natives (native MessageQueue/epoll glue, Looper, Choreographer's DisplayEventReceiver, Canvas/Bitmap/HWUI natives, Parcel natives).
6. **HWUI render pipeline** (RenderNode/DisplayList/Skia) and the display stack (SurfaceFlinger/BufferQueue/GRAlloc) — or a software-canvas path (MiniAndroid's ladder probe already proves its software canvas is color-exact).
7. **android.os.Looper native event loop** (epoll-based message queue) + **Choreographer vsync source** — Compose's `withFrameNanos`/recomposer loop sits on this.
8. **App glue chain in framework.jar**: ActivityThread → LoadedApk → ContextImpl → Instrumentation → Application (these are framework classes, i.e. layer 1, but listed because Compose apps specifically need ViewRootImpl + Choreographer + window insets chain).
9. **bionic-vs-glibc deltas** for ART itself (solved for host build; ART host already compiles against glibc) and for app native libs (linker namespaces, libnativeloader — MiniAndroid already runs its own gcc-built .so probe).
10. **APEX runtime modules**: conscrypt (TLS), ICU data, tzdata — hostdex variants exist for tests only.
11. **ashmem/memfd + misc OS services** surfaced through PAL (PaletteAshmemCreateRegion etc. — on plain Linux, memfd is the substitute).

Count: **11 named layers**; layers 1–3, 5 are the giant ones and are exactly MiniAndroid's existing shadow/framework/bridge surface re-expressed as guest-executable code.

---

## 4. "Has anyone done Compose-on-host without Android?" — verdict

**No, for real APKs.** Verified landscape:
- **Compose Desktop / Compose Multiplatform (JetBrains)**: Compose runtime + Skia (skiko) on desktop JVM — but the UI is compiled from Kotlin source to JVM bytecode; it cannot load an APK; no android.* framework. (Source-based only.)
- **Robolectric (+Roborazzi, + Compose UI tests)**: real Compose UI rendering on a host JVM with real AOSP framework classes and native Skia (RNG) — the closest thing to "Compose on host without Android OS" that exists in open source — but it consumes Gradle-built JVM classes, never APK DEX.
- **Westlake**: real APKs, real VM, non-Android host OS — but View-based only; no Compose runtime in its shims.
- **Anbox/Waydroid/redroid/etc.**: Compose apps run, but inside a full Android OS (premise violated).
- **Alien Dalvik**: reportedly runs modern apps (incl. Compose era) on non-Android platforms — proprietary, unverifiable.
- Searches for "compose desktop run android apk", "run android app on linux no emulator", "gemini apache celadon app mode", "cuttlefish without emulator" surfaced **no open-source APK-loading Compose-on-host project** (only emulators/containers/guides, and zero results for any "celadon app mode").

**MiniAndroid is plausibly first** for "real Compose APK, desktop Linux, no Android OS"; the components to get there exist separately (real VM execution: ART-host/dalvik-universal; Compose-on-host semantics: Robolectric/Compose Desktop; framework-as-guest: Westlake — each Apache-2.0).

---

## 5. Bridge-size estimate for MODE B (external DEX/JVM execution + MiniAndroid Android-API bridge)

Reference points (measured, not guessed):
- Westlake (real APKs, View apps): **2,056 shim classes** (2,479 java files), **193K lines** unmodified AOSP framework code + 134 dependency stubs for View/TextView/ViewGroup/AbsListView/ListView alone (62,153 lines), **~25 C bridge functions / ~15 HAL boundaries**, libcore natives ~30 (+ zlib, ICU regex, JarFile, Character, Typeface stubs), MiniServer+MiniActivityManager replacing system_server.
- dalvik-universal: ~4,000-class java.* boot classpath + 1,658-line libcore_bridge (30+ natives).
- ART host: PAL = 21 OS methods; libcore boot jars prebuilt (`-hostdex`).
- MiniAndroid today: the entire framework bridge already exists as shadows (dooz run: 33,460 stub calls at one frame window; registry shows ~566 generic semantic roots over a 12-app corpus).

What MODE B requires:
1. **A real VM**: dalvik-universal (~250K LOC C/C++, Apache-2.0, already 64-bit) or ART host (700K+ LOC C++, Apache-2.0, current DEX). The VM itself is free; the risk differs (038-opcode gap vs. size).
2. **Guest-side android.* layer** — two designs:
   - (a) *Westlake-style*: android.* implemented as real Java/DEX classes inside the VM, calling ~15–30 host boundaries. Need ≈ **2,000–2,800 classes** (Westlake's 2,056 + android.graphics/Canvas/Paint/Path/Bitmap/Typeface, android.text/StaticLayout, android.os/Choreographer, animation — the Compose dependencies), ≈ **100–200K lines**, of which MiniAndroid's existing shadow semantics are the spec (re-expression, not invention).
   - (b) *Per-call JNI bridge out to MiniAndroid shadows*: ≈ **8,000–20,000 distinct native method registrations** (bounded by MiniAndroid's current shadow-method surface; dooz's 33,460 stub calls indicate call volume, not surface) — and the killer: **identity mapping** (every shadow must become a guest object or handle with lawful equals/hashCode/monitor/Class/generics/reflection; MiniAndroid's own registry — ~566 roots in 12 apps, several specifically identity/reflection laws like F-NEW-224/253/257 — is the empirical bug density: expect ~1 generic root per 60–100 bridged classes).
3. **Native/primitive set**: ≈30–60 bridge functions (surface/framebuffer, input, timers/vsync, memory, I/O) — MiniAndroid already owns all of these; Westlake proves ~25 suffice for View apps; Compose adds vsync/frame-clock fidelity.
4. **Threading/JNI**: guest Looper on host epoll; Dispatchers.Main→Handler→Choreographer round-trip; thread attach/detach for every MiniAndroid thread entering guest code.
5. **Numeric bottom line**:
   - dalvik-universal variant: VM integration 250K LOC (given) + 2,000–2,800 shim classes / 100–200K lines (mostly transcribable from existing shadow semantics) + 30–60 C bridges + identity law. **≈6–12 engineer-months** to reach corpus parity; residual risk: DEX-038-only opcodes from modern R8 (invoke-custom, string-concat invokedynamic) unhandled in KitKat interpreter.
   - ART-host variant: same shim work + PAL host impl + boot-image plumbing on 700K LOC C++. **≈12–24 engineer-months**; kills the DEX-version and Kotlin-semantics risk outright (interpreter handles invoke-custom; libcore is current).
   - The bridge is the same API surface MiniAndroid already implements — MODE B does not add API surface, it changes *who executes the bytecode* and forces the identity law to be explicit (guest objects are real, shadows become services).

---

## 6. Sources not verifiable / limitations

- **GitHub API core endpoints: rate-limited to 0** (reset epoch 1791335887) — repo trees/issues fetched via raw.githubusercontent.com, codeload tarballs, and search API instead. Search API quota limited total searches (~10 used).
- **android.googlesource.com "+log" pages: 403 Forbidden (sign-in required)**; some `?format=TEXT` paths 404 (libartpalette/README.md, test/README.txt do not exist upstream).
- **web-search upstream 429s** on several queries (ART standalone, dalvik vm c++, jamvm, celadon) — retried with reworded queries where possible; the "jamvm" web-search verification failed entirely (evidence above is from GitHub repo metadata instead).
- **"gemini apache celadon app mode"**: zero relevant results — existence of any such mode could NOT be verified (treated as nonexistent).
- **A2OH/westlake `dalvik-port/` directory is empty in the clone** (possibly LFS/submodule/removed) — the claim that the ARM64 JIT dalvikvm build lives there could not be source-verified; README and ohos-deploy references are the evidence.
- **dalvik-universal test claims** (2,416 headless tests, MockDonalds 14/14, real-APK pipeline) are README statements; test sources exist in-tree (tests/, unit-tests/) but were not executed here.
- **Alien Dalvik**: proprietary — no source evidence obtainable, marketing/forum data only.
- **dooz-version facts** (compose 1.11.4, kotlinx 1.9.0) are taken from the project worklog (CONT-10), not re-derived.
