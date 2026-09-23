# MINIANDROID EXTERNAL RUNTIME INDEX (WS-C5)

**Quick index table — details in `MINIANDROID_EXTERNAL_RUNTIME_KNOWLEDGE.md`**

| # | Project | Runs real APK? | Android OS? | Emulator/KVM? | CPU-only headless? | Screenshot | UI tree | Input | Deterministic | Sandbox | License | Class for us |
|---|---------|----------------|-------------|---------------|--------------------|------------|---------|-------|---------------|---------|---------|--------------|
| 1 | Robolectric | ❌ (app JVM bytecode, not APK) | ❌ | ❌ | ✅ | ✅ (RNG) | ✅ | ✅ (synthetic) | ✅ (@Resetter/paused looper) | sandbox classloader | MIT | **ARCHITECTURE TEMPLATE** |
| 2 | Paparazzi | ❌ (View/Compose JVM) | ❌ | ❌ | ✅ (layoutlib) | ✅ PNG/APNG | ✅ (a11y overlay) | ❌ | ✅ (pinned env) | in-process | Apache-2.0 | RENDER REFERENCE |
| 3 | Roborazzi | ❌ (on Robolectric) | ❌ | ❌ | ✅ | ✅ | (from Robolectric) | (from Robolectric) | ✅ | ✅ | Apache-2.0 | CAPTURE PATTERN |
| 4 | DSH Android | ❌ (adb harness) | ✅ required | AVD/device | ❌ | ✅ (stream) | ✅ (+OCR) | ✅ | ❌ | ❌ | MIT | AGENT TOOL SURFACE |
| 5 | J-Code Android | ✅ (on device) | ✅ | ❌ | ❌ | (device capture) | ❌ | ❌ | ❌ | ❌ | UNVERIFIED | LOW VALUE |
| 6 | Emulator Harness/Cuttlefish | ✅ (full system) | ✅ | ✅ KVM | ❌ | ✅ | (instrumentation) | ✅ | snapshot/restore | ✅ | Apache-2.0 | OPS FEATURES |
| 7a | Redroid | ✅ (real ART) | ✅ (container) | ❌ KVM not needed | ⚠️ needs kernel binder+memfd | ✅ scrcpy | ❌ | ✅ adb | ❌ | container | Apache-2.0* | KERNEL-DEP MAP |
| 7b | roidy | ❌ (adb frontend) | ✅ (device) | ❌ | ❌ | ✅ terminal | ❌ | ✅ | ❌ | ❌ | MIT | VIRTUAL-DISPLAY PATTERN |
| 8 | VirtualApp | ✅ (on device, host ART) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | VA-space | dual/commercial | SERVICE PROXY MAP |
| 9 | Evoke | ✅ (on device, API 31+) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | stub processes | **0BSD** | MODERN VA REFERENCE |
| 10 | AppManager | ❌ (inspector) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | — | — | GPLv3+ | DEX TOOLING (dexlib2) |
| 11 | GameNative | ❌ (Windows game/Wine) | ✅ (host) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | MIT | OUT OF SCOPE |

*Redroid license UNVERIFIED at file level.

## Statistical summary
- "Real APK without Android": **zero projects** in the entire survey (confirms MiniAndroid's niche)
- Closest adoptable models: Robolectric (architecture) · RNG/Paparazzi (rendering) · cuttlefish (snapshot) · DSH/roidy (agent tools) · Evoke 0BSD (copyable reference code)

# WS-C5 PRIMARY TRANSFER

**To:** Primary Coder · **From:** WS-C5 · **Date:** 2026-08-27

## P1. Build the "Environment" architecture at the runtime level (Robolectric pattern)
- controllable clock + paused-looper mode + complete-state reset between runs
  → determinism sturdier than the current "3-run SHA" (which fortunately works but
  is not a structural guarantee). CONFIDENCE: HIGH · RISK: MED (internal rework)
- EVIDENCE: Robolectric AndroidTestEnvironment/@Resetter (§1 knowledge)

## P2. Consolidate the interception list in one place
- VirtualApp proxies/ + Evoke hooks + Robolectric's 607 shadow clusters →
  the map of "services that must be simulated". Then close F007/F010 in a targeted way.
- ACTION: a one-page doc `SERVICE_INTERCEPTION_MAP.md` in the repo.

## P3. Snapshot/restore between runs
- memory/heap/sandbox state → file; reload for faster debugging
  (the cuttlefish pattern). CONFIDENCE: MEDIUM (real engineering work)

## P4. The agent-facing tool surface
- install/launch/screenshot/input-by-id/logcat/memory as separate CLI
  subcommands (the DSH pattern). MiniAndroid already has almost all of it — just
  make it uniform. BENEFIT: LLM-agent use (exactly your use case).

## P5. Native-as-data is a proven path
- Robolectric dlopens `libnativeruntime.so` (SQLite+Skia) →
  the concern about "C libs in a C++ runtime" is unfounded; do D1 (SQLite).

## THINGS NOT TO DO
- Do not go for KVM/containers (redroid/cuttlefish) — outside the headless CPU-only mission
  and exactly what MiniAndroid does not need.
- Do not use VirtualApp as a dependency (frozen/dual-license) — only
  read its proxy checklist. Evoke (0BSD) is free for code study.
