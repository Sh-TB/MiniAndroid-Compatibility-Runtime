# MiniAndroid — Headless Android APK Compatibility Runtime

**Version:** 0.13.0 + master reconciliation (integration branch `integration/master-reconciliation`)
**Date:** 2026-09-02
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (MASTER — this is the project's own source of truth, not a fork)
**License:** MIT

---

## PROJECT — What is MiniAndroid?

MiniAndroid is a **research-grade Android APK compatibility runtime written from
scratch in C++17**. It parses real APK files (ZIP + DEX + `resources.arsc` + binary
XML), executes real Dalvik bytecode with a register VM, bridges Android framework
APIs through a shadow layer, inflates real layouts into a view tree, and renders
frames to a software framebuffer with deterministic, hash-pinned pixel evidence.

**Acceptance criterion since day one: real APKs, real bytecode, byte-stable evidence.**
A capability is PROVEN only when a re-runnable artifact reproduces it.

| Feature | Android Emulator | MiniAndroid |
|---------|-----------------|-------------|
| Runs real DEX bytecode | ✅ | ✅ (C++ register VM — no JVM/ART) |
| Requires GPU / KVM / HAXM | ✅ | ❌ (CPU software rendering) |
| Deterministic re-runs | ❌ | ✅ (hash-pinned goldens) |
| Direct heap / view-tree visibility | ❌ | ✅ |
| AI-agent click/text dispatch | ❌ | ✅ (click-test probe, second-frame diffs) |
| Startup | tens of seconds | < 1 s per APK |

---

## ARCHITECTURE (all subsystems under `miniandroid/src/`)

```
APK file (external cache, never committed)
  └─ apk/apk_parser.cpp, manifest_reader.cpp      ZIP (streaming, data descriptors, CRC)
       └─ resources/arsc_parser.cpp               resources.arsc: string/type/key tables,
       └─ resources/axml_parser.cpp               binary XML → real layout inflation
       └─ resources/layout_inflater.cpp           (non-obfuscated trees; guarded fallback
       └─ resources/resource_runtime.cpp           for obfuscated res/0s.xml)
            └─ dex/dex_parser.cpp                 multi-DEX (Telegram = 5 DEX, 12,544 classes)
            └─ dex/class_resolver.cpp             class/superclass graph, per-DEX string resolution
            └─ dex/dalvik_engine.cpp              ★ register VM: fetch-decode-execute, opcode
            └─ dex/dex_interpreter_batch.cpp        table, exception system, invoke bridges
                 └─ framework/android_shadows.cpp 95+ bridged framework classes (shadow layer)
                 └─ framework/shadow_registry.cpp  type-aware stub defaults
                 └─ framework/dialog_shadow.cpp    dialog/window object model
                 └─ framework/canvas_shadow.cpp    Canvas ops incl. save/restore/translate/
                 │                                  scale/rotate/skew/concat/clipRect
                 └─ runtime/execution_engine.cpp   journey stages, click dispatch, probes
                 └─ renderer/software_renderer.cpp framebuffer → PNG; text via BitmapFont,
                 │                                  images via libpng/libjpeg/libwebp, Lottie via rlottie
                 └─ api/, storage/                 context, SharedPreferences (persisted), file sandbox
                 └─ diagnostics/                   api_trace.json, click frames, traces
```

Async/Handler: FIFO handler-queue semantics are fixture-proven (23/23);
timers exist but corpus triggers remain thin.

---

## VERIFIED CAPABILITIES (evidence-backed, re-runnable)

| Capability | Evidence |
|---|---|
| Deterministic Telegram v12 journey (41,233 non-white px) | golden `088ea640…` (3/3 in 011.x campaigns). ⚠️ golden APK SHA `f5e11927…` lost from external cache 2026-09-02; current telegram.org serves newer bytes → re-assertion pending APK re-acquisition |
| SimpleStopwatch pixel-exact golden | `2a12587a…` BASELINE_MATCH — preserved across campaigns 011.2→013 **and** through the 2026-09 semantic fix |
| Real layout inflation + ARSC resolution | ARSC probe: 58 entries, 3/3 layouts (simplestopwatch); gmdice 73 named ids |
| Click → listener → state → second frame | gmdice 4/4 clicks, simplestopwatch 2/2, bouncy 10/12 (click_test_report.json) |
| Multi-DEX execution | Telegram 5 DEX; WhatsApp/Signal probes executed |
| Semantic core (64-bit long, cmp, conversions) | `tests/semantic_long_cmp_conv_test.cpp` **14/14** (fixed 2026-09-02, see MASTER_PROJECT_KNOWLEDGE) |
| Typed exception catch + propagation | `tests/unified0113_typed_catch_test.cpp` **8/8** |
| filled-new-array 35c nibbles | `tests/unified0112_filled_new_array_test.cpp` **5/5** |
| Handler/Looper FIFO ordering | `tests/exp088_phasef_handler_queue_semantics.cpp` **23/23** |
| PNG/JPEG/WebP decode, Lottie render | EXP-096/097/098 evidence + rlottie wired on SMS screen |
| View hierarchy / prefs / file sandbox | `tests/simple_test.cpp` 4/4, storage tests |

---

## PARTIAL CAPABILITIES (implemented, incomplete or not fully proven)

- **Opcode/API long tail** — interpreter covers the corpus-proven set; see
  `miniandroid/TEST_MATRIX.md` and EXP-032 coverage docs.
- **Layout geometry** — weight distribution bugs (simplestopwatch full-height buttons).
- **Fonts** — BitmapFont renders; overlap on long strings (SFS-010); FreeType+HarfBuzz+FriBidi
  RTL pipeline is POC (6/6 Persian samples), not yet the TextView path.
- **GLES/EGL** — PortableGL glue adopted (golden cube 1,668 fps @320×240) but GLSL
  execution + dispatch hook NOT wired: GLES apps still render through the Canvas path.
- **Canvas matrix** — ops accepted and recorded (RESULT_014); full matrix-composition
  semantics not exhaustively proven.
- **Audio** — engine + stb_vorbis/minimp3 recovered from UNIFIED_005/008; not in default build.

---

## KNOWN BLOCKERS (real, current)

1. **Compose apps (Dooz)** — blank frame `31ddd4d5…`: ComponentActivity.setContentView
   reached, ComposeView created with 0 children; composition boundary not crossed.
2. **GLES dispatch hook** — GLSurfaceView/EGL render loop not connected (see GLES_REPORT_013.md).
3. **Obfuscated resources** — `res/0s.xml`-style trees abort safely (guarded).
4. **packed-switch/sparse-switch (0x2B/0x2C)** — opcodes defined, NOT dispatched
   (verified 2026-09-02; falls to handle_unimplemented).
5. **String bridge gaps** — `Integer.parseInt`, `Long.parseLong`, `Float.parseFloat`,
   `Double.parseDouble`, `String.substring`, `String.concat` are NOT implemented in
   the production dispatch (verified 2026-09-02; exp018's "NATIVE_CPP" list was a plan).
6. **div-long/rem-long by zero** — returns 0; real Android throws ArithmeticException.

---

## HISTORICAL ACHIEVEMENTS (knowledge preserved — code may be superseded)

- **EXP-001 → EXP-101 era** (commits `1c5255a`…`bbe0ce3`): corpus mining, DEX pipeline,
  Telegram journey, ZIP/AXML/ARSC, PNG pipeline, click dispatch, WebP/JPEG/Lottie.
- **UNIFIED_011 → 011.3**: repository recovery, typed catch, FNA fix, IMAGE-RES-RENDER,
  click-test probe, goldens pinned.
- **CAMPAIGN 013** (`v0.11.4-fix-01`…`v0.13.0`): dialog/window model, hierarchy shadow
  dispatch, ARSC file-backed value path, real onDraw(Canvas) for custom views.
- **CAMPAIGN 014** — PARTIAL: triage evidence for 16 apps archived in
  `docs/campaign014_evidence/`; code commits lost (see CAMPAIGN_014_STATUS_PARTIAL.md).
- **2026-09 master reconciliation** (this branch): 353-commit history unified,
  semantic core verified+fixed (RESULT_001/007/009/010), zero regression.

Full history: `MASTER_CHANGELOG_AND_KNOWLEDGE.md`, `MASTER_PROJECT_STATE*.md`,
`miniandroid/docs/` (129 documents), `miniandroid/docs/knowledge/` (workstream transfers),
campaign indexes `campaign005/006/008/009/010/011`.

---

## CURRENT ROADMAP (attack order)

1. String bridge: `parse*`, `substring`, `concat` (unlocks ~20% corpus paths — EXP-018 data).
2. packed-switch/sparse-switch dispatch.
3. Compose composition hook (cross the Dooz blank-frame boundary).
4. GLES dispatch hook (SurfaceView/EGL render loop).
5. Layout weight/measure correctness.
6. div-long zero → ArithmeticException (with typed-catch infra this is now cheap).
7. Re-acquire Telegram v12 golden APK; re-assert `088ea640` baseline.

---

## VALIDATION RULES — how this project defines PROVEN

1. **Real APKs** from the external cache (`MINIANDROID_APK_CACHE`, never committed).
2. **Pixel evidence**: screenshots hashed (SHA-256), compared against pinned goldens.
3. **Determinism**: identical re-runs (×3 for goldens).
4. **Discrimination**: a regression fixture must FAIL on the old code, PASS on the new.
5. **Zero regression**: every fix re-runs the matrix + goldens; changes are documented, never hidden.
6. History shallow-note: lineage below `a9434de` was cut by a 2026-09 cache event and
   re-unified from the GitHub master; `f5da664/v0.12.0` never existed (see GIT_PROVENANCE_RESOLUTION.md).

## AGENT RULE

Agent/analysis reports are **DISCOVERY / LEAD**, never PROOF. Pipeline:
AGENT CLAIM → source inspection → runtime-path analysis → reproduction where
possible → independent validation → classification (VERIFIED / VERIFIED+FIXED /
PARTIALLY VERIFIED / ALREADY FIXED / NOT REPRODUCED / FALSE / UNKNOWN /
ANALYSIS ONLY) → implement only if justified.
Concrete example: exp018 listed `Integer.parseInt` as "NATIVE_CPP" — 2026-09
source inspection proved it was never implemented (see AGENT_DISCOVERIES.md).

## REPRODUCIBILITY

```bash
# external APK cache (NO APKs inside the repo, ever)
export MINIANDROID_APK_CACHE=/path/to/apk_cache
python3 miniandroid/scripts/download_test_apks.py        # SHA-verified fetch

# rlottie (only external lib not in system packages)
git clone https://github.com/Samsung/rlottie /home/z/my-project/tools/rlottie
cmake -S /home/z/my-project/tools/rlottie -B /home/z/my-project/tools/rlottie/build \
      -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DBUILD_SHARED_LIBS=OFF
cmake --build /home/z/my-project/tools/rlottie/build -j
# Makefile expects librlottie.a at .../build/src/ — copy if cmake emits .../build/

cd miniandroid && make -j          # → build/miniandroid

# canonical matrix + goldens
python3 miniandroid/scripts/u011_test_matrix.py
# expected: simplestopwatch 2a12587a… BASELINE_MATCH

# semantic fixtures (link pattern: fixture.cpp + all build/**/*.o minus main.o)
# see VERIFIED_TESTS.md for exact commands and expected results
```
