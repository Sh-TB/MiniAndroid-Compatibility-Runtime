# MINIANDROID EXTERNAL RUNTIME KNOWLEDGE (WS-C5)

**Date:** 2026-08-27 · source: WS-C5-RESEARCH (web + repos) · uncertain items: UNVERIFIED
**Core charter question:** which external architectures execute real APKs without Android OS / KVM / GPU, and what lessons do they hold for MiniAndroid?

## Strategic synthesis (the campaign's most important result)

**No known project executes a real APK/DEX on plain Linux without Android.** The space splits three ways:
1. **JVM simulation** — Robolectric/Paparazzi/Roborazzi: real Java framework code + the app's JVM bytecode + interception at the native/service boundary.
2. **Container/VM** — redroid/Waydroid/cuttlefish/emulator: real ART but needs binder/memfd or KVM.
3. **MiniAndroid's niche** — DEX interpretation in C++ + real lifecycle + rendering + screenshot, with none of those dependencies → **a genuinely empty space**; closest templates: the Robolectric architecture (sandbox/intercept/reset) + RNG/Paparazzi rendering (real rasterizer + fonts/ICU as data).

---

## 1. Robolectric — deepest analysis
- github.com/robolectric/robolectric · MIT · 4.16.1 (2026-01) · very active (Google) · ~110,646 LOC Java, **607 shadow classes**, API 23–36 support.
- **Execution:** real AOSP framework code (the `android-all-instrumented` jars, rewritten at publish time by `ClassInstrumentor`: every method → invokedynamic delegator; natives → shadowable) + the app as JVM bytecode. **It does not parse APKs.**
- **No OS/emulator/KVM/GPU** — JVM only; natives: real SQLite (`SQLiteMode.NATIVE` → `libnativeruntime.so`) + Robolectric Native Graphics (RNG, Skia) as per-OS `.so` files inside resources, dlopen'd at runtime.
- **Mechanism:** `SandboxClassLoader` (loads the instrumented framework first, preventing the "fake Android!" stub) · `ShadowMap`+`ShadowWrangler` (dispatch to shadows) · `AndroidTestEnvironment` (Looper/Resource/Manifest/display/ActivityThread simulation) · `@Resetter` (state reset between tests → determinism) · default PAUSED scheduler with a controllable clock.
- **Output:** real View hierarchy, real LayoutInflater, real CPU rendering + screenshots (consumed by Roborazzi), official UI Simulator.
- **Lessons for MiniAndroid:**
  a) intercept only at narrow boundaries (system services, JNI, libcore-delta) — a small, enumerable surface;
  b) environment simulation must be a first-class component (clock/resource/display);
  c) real natives (SQLite/Skia) as binary+dlopen on plain CPU is feasible;
  d) full state reset = determinism.

## 2. Paparazzi (cashapp) — headless rendering with layoutlib
- 2.0.0-alpha05 (2026-05, layoutlib v16.2.1) · Apache-2.0 (UNVERIFIED at file) · active.
- Runs real View/Compose on the JVM and renders with **layoutlib** (the same engine as Android Studio) — no emulator/GPU.
- Key files (master): `Paparazzi.kt`, `PaparazziSdk.kt`, `internal/Renderer.kt`, `agent/InterceptorRegistrar.kt` (ByteBuddy), diff engines `PixelPerfect/Mssim/DeltaE2000`.
- PNG/APNG screenshots + accessibility-tree overlay; **no input injection** (single frame).
- **Lesson:** Studio-quality rendering without Android is possible with "framework jar + Skia native + fonts/ICU as data + SessionParams"; the diff engines are the model for our image comparison.

## 3. Roborazzi (takahirom) — proof of "real UI → real pixels → PNG" on CPU
- 1.73.0 (2026-08) · Apache-2.0 (verified) · hyperactive.
- On Robolectric + **RNG** (`@GraphicsMode(NATIVE)`); capture at the Canvas/Bitmap level → PNG/GIF + record/verify/compare in CI.
- **Lesson:** put capture at the canvas/bitmap level, not the "whole screen".

## 4. DSH Android (ZSeven-W/dsh-android)
- 0.1.0-rc.4 (2026-08) · MIT. **An LLM tooling plugin for adb** (not a runtime): 20 tools (build/run/screenshot/tap-by-id/OCR/logcat/memory) against a real device.
- **Lesson:** the agent-facing tool-surface layout for MiniAndroid (install→launch→screenshot→input→logcat→memory) + the signed-URL frame streaming pattern.

## 5. J-Code Android (blamspotdev/j-code-android)
- An Android IDE (2026-05, 8 stars); runs APKs via **the device's own normal runtime + ADB bridge + JDWP**; proot for the toolchain. Outside the headless domain. **Lesson:** "run in a tab" UX and JDWP; low architectural value.

## 6. Android Emulator Harness (google/android-emulator-container-scripts + Cuttlefish)
- Runs the **full Android system**; requires: Docker + **KVM** (nested-virt in cloud) · WebRTC streaming · snapshot/restore (cuttlefish).
- **Lesson:** the fidelity floor; valuable harness features: snapshot/restore, an adb-compatible control plane, streaming.

## 7a. Redroid (remote-android/redroid)
- Android 11–16 in Docker **without KVM**; kernel requirements: `binder_linux` + ashmem/memfd; GPU optional (software fallback ~15fps).
- Install/run: `adb install` + `am start`; imaging: scrcpy/screencap; overlayfs for each instance's data.
- **Lesson:** the precise list of kernel dependencies "real Android" needs → the IPC/shared-mem equivalents MiniAndroid must simulate; the per-instance operational pattern.

## 7b. roidy (sanohiro/roidy)
- MIT, 2026-03. A terminal adb front-end: per-app virtual display + kitty-graphics.
- **Lesson:** "one virtual display per task/Activity" is a good pattern for a headless runtime.

## 8. VirtualApp (asLody) — public repo frozen in 2017, separate commercial version
- Runs real APKs **on device** by importing them into VA-space; `VirtualCore`/`InvocationStubManager`/`VClientImpl` + stub-component swap in H-messages; per-service proxies.
- **Lesson:** the most complete empirical checklist of "what an app touches in a runtime" (AMS/PMS/H-order/Provider/AppOps/clipboard) → a roadmap for service simulation.

## 9. Evoke (smartdone/Evoke)
- 0BSD! (verified) · 2026-03 · minSdk 31, tested on Android 16. A modern VirtualApp successor with `core-virtual` + `core-native` (Frida Gum, I/O redirect).
- **Lesson:** the new Java-proxy ↔ native-hook boundary on modern Android; copyable code (0BSD) for the patterns.

## 10. AppManager (MuntashirAkon/AppManager)
- GPLv3+ · an on-device APK inspector; uses **dexlib2/baksmali** + a jadx fork + an apksig fork.
- **Lesson:** dexlib2 as the reference model of the DEX format for cross-checking our parser (§ WS-C4→C3).

## 11. GameNative (utkarshdalal/GameNative)
- MIT, 10.1k stars · a launcher for **Windows** games on Android (Wine) — outside the DEX domain. Lesson: wrapping a heavy runtime.

---

## 12. Supplementary findings (BONUS)
| Project | What it is | Lesson |
|---|---|---|
| jserv/simple-dvm | an educational mini Dalvik VM in C | a small, understandable interpreter core |
| IlyaGulya/rust-dalvik-vm | a DVM in Rust (2024) | proof of our approach's viability |
| wangziqi2013/Android-Dalvik-Analysis | a C++ DEX parser/disassembler | a direct C++ reference for the loader |
| WanghongLin/StandaloneDVM | standalone dalvikvm | Dalvik portability history (details UNVERIFIED) |
| akavel/dali | a Nim DEX assembler | a format reference |
| Waydroid / Anbox | full Android in LXC + binder + Wayland | why they don't fit: kernel/Wayland/heavy; Anbox abandoned |
| DroidRun (9.1k) / arbigent (633) / Mobile-Agent | LLM agents testing UI with accessibility/screenshot | future consumers of our runtime; arbigent also has a Robolectric mode |

---

## GAP ANALYSIS for MiniAndroid (from the synthesis)
1. **Environment simulation** (clock/pausable Looper/resource/display) — model: Robolectric AndroidTestEnvironment.
2. **Interception map** — a single list of the proxyable services (VirtualApp proxies/ + Evoke hooks + Robolectric's 607 shadows → a small number of clusters).
3. **Real natives as data** — SQLite (D1), later a Skia-class raster (REFERENCE: RNG).
4. **Capture at the canvas level** — the Roborazzi pattern.
5. **Snapshot/restore** — the cuttlefish pattern for state between runs.
6. **Agent tool surface** — install/launch/screenshot/input/logcat/memory as separate tools (DSH/roidy/DroidRun).
