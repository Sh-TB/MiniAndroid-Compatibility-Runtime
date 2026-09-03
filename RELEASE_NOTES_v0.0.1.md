# Brahma — MiniAndroid v0.0.1 — First Public Release

**Date:** 2026-09-03 · **Release commit:** see tag `v0.0.1` · **Source anchor:** `02e72ae`
**Artifacts:** `MiniAndroid-v0.0.1-Brahma-linux-x64.tar.gz` · `MiniAndroid-v0.0.1-Brahma-windows-x64.zip` · source archives

---

## What MiniAndroid is

MiniAndroid is a from-scratch Android APK compatibility runtime in C++17.
It runs real Dalvik bytecode from real APK files in a register VM — no JVM,
no ART, no emulator, no GPU — bridges the Android framework through a shadow
layer, inflates real layouts, and renders deterministic software frames with
SHA-pinned pixel evidence. A capability is claimed only when a re-runnable
artifact reproduces it.

## What is now proven

- **144/144 semantic fixture cases PASS** at this commit (8 discriminating suites, each failing on pre-fix code): string/parse bridges, packed/sparse-switch, 64-bit arithmetic & conversions, typed exceptions, filled-new-array, return-wide, handler-queue FIFO async, view basics.
- **5 deterministic golden baselines** — simplestopwatch `2a12587a…` is a pixel-exact law preserved across every campaign and the 2026-09 semantic fix; gmdice/microtimer/unote byte-stable; dooz = documented deterministic BLANK (Compose boundary).
- **Real interaction loop**: click → listener dispatch (`onButtonStart`/`onButtonReset`) → state mutation → second frame differs by exactly 12,439 pixels.
- **Resource stack**: ARSC parsing incl. obfuscated file-backed values, AXML parsing, real layout inflation, custom-view `onDraw` execution.
- **Rendering paths**: software framebuffer with PNG/JPEG/WebP image decode and rlottie Lottie playback.
- **Multi-DEX**: 5-DEX APK class loading (Telegram-class scale, 12,544 classes).
- **Dialog/Toast/window object model** with stacked-window compositing (gmdice two-dialog chain pixel-verified).

## Major runtime improvements (2026-09 reconciliation → GAME_CHANGER)

- Whole 0x7B..0x80 opcode family implemented; lit8 opcode table re-aligned to AOSP (was shifted — `add-int/lit8` dispatched as AND).
- `Integer.parseInt`, `Long.parseLong`, `Float.parseFloat`, `Double.parseDouble`, `String.substring`, `String.concat` now dispatch with strict Java semantics (0/25 → 25/25).
- packed-switch (0x2B) / sparse-switch (0x2C) payload dispatch — both shapes.
- `div-long`/`rem-long` by zero now throws `ArithmeticException` (was silent 0; also removed unguarded C++ UB in the int/2addr form).
- Dialog/Toast rendering path, superclass-chain app-class dispatch, inflation rejection guard, ARSC value-first resolution, custom-view onDraw (FIX-013-01..05).

## DEX execution progress

Register VM covers the corpus-proven opcode set with typed exception
propagation, per-DEX string resolution, and a class/superclass graph. The
engine core (`dalvik_engine.cpp`, ~745 KB) executes the full 5-APK matrix
with exit 0 and byte-stable screenshots.

## Rendering / resource progress

Deterministic PNG output from a software framebuffer; android:src icons
decode and render for real; ARSC value-first path resolution handles
AGP-obfuscated trees; real AXML layout inflation replaces synthetic screens
whenever a real tree exists.

## Interaction / lifecycle progress

Journey stages (Application.onCreate → Activity → layout → first frame →
click frames) execute through the superclass-chain shadow dispatch; click
probes produce second-frame pixel diffs and state-change evidence
(`run/click_test_report.json`).

## Test / evidence coverage

- 144/144 fixtures (see `VERIFIED_TESTS.md` for exact commands & expected SHAs)
- Canonical matrix + 5 goldens, ×3 determinism rule
- ARSC probe on a real APK ("arsc valid", layouts 3/3)
- Multiframe click test with pixel-diff accounting
- Full pre-push audit: clean-extraction rebuild + re-run of everything above from the published archive alone

## Known limitations (transparent)

Compose runtime boundary (deterministic BLANK on dooz); GLES dispatch hook
unwired (Canvas path serves GLES apps); layout weight geometry wrong;
long-string font overlap; RTL pipeline POC (not TextView path); audio engine
not in default build; Telegram v12 golden APK lost (journey not reproducible
until re-acquired); Campaign 014 runtime code lost (triage evidence only);
Canvas matrix composition tests incomplete; WhatsApp/Signal single-run only.
Details: `NOT_DONE.md`, `TOP_BLOCKERS_013.md`.

`READY_FOR_PUSH` / this release means **repository safe to publish** — it is
not a claim that the project is feature-complete.

## Quick start — Linux

```bash
tar xzf MiniAndroid-v0.0.1-Brahma-linux-x64.tar.gz
cd MiniAndroid-v0.0.1-Brahma-linux-x64
./run-miniandroid.sh run /path/to/your.apk -o ./frames -v
```

Prerequisites: x86-64 Linux; glibc ≥ 2.38 and libstdc++ from GCC 13.x
(build box: Ubuntu 24.04 — on older distros, build from source); dynamic
libs libpng16, libjpeg.62, libwebp, zlib. FreeType/HarfBuzz/FriBidi/rlottie
are statically linked. No JVM/GPU/KVM.

## Quick start — Windows

`MiniAndroid-v0.0.1-Brahma-windows-x64.zip` is an honest **build kit**
(source + build scripts + instructions), not a prebuilt `.exe` — read
`BUILD-WINDOWS.md` inside for MSYS2/MinGW-w64 prerequisites and exact
commands. It was not possible to smoke-test on a real Windows host from the
build environment; the kit is therefore labeled accordingly.

## Feedback / issue reporting

Please open issues at
https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues — include
the APK name, the command line, and (if available) the SHA-256 of the output
screenshot; the runtime writes `api_trace.json` and click frames next to the
output, please attach them. Deterministic reproduction is the project's
language — reproduce first, argue second.
