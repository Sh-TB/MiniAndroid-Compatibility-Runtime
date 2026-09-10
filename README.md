# MiniAndroid — a from-scratch Android APK Compatibility Runtime

**Current Release:** `v0.0.3 — Chantecler` (Compose execution frontier + root-law closure, 2026-09-10)
**Previous:** `v0.0.2 — Australorp` (real-APK execution proof, 2026-09-04) · `v0.0.1 — Brahma` (2026-09-03)
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (master, not a fork)
**License:** MIT

---

# Latest Verified Progress

| Field | Value |
|---|---|
| **HEAD** | M8 commit (F-050 family; see `docs/ROOT_DISCOVERY_INDEX.md` for the exact hash after push) |
| **DATE** | 2026-09-10 |
| **BATTERY** | **91 stages — ALL PASS** (88 + F-050 build/run/golden) |
| **REAL APK** | 13-app open-source corpus + lighthouse dooz `d81292cd…` (SHA-pinned) |
| **PROVEN ROOTS** | F-028, F-028h, F-029, F-030, F-031..F-033, F-035, F-036, F-039, F-040, F-041, F-042, F-043, F-044, F-045, **F-050a (Choreographer frame pump — new)**, **F-050b (Throwable message law — new)**, **F-050c (AtomicLongFieldUpdater getAndIncrement — new)**, **F-050d (Boolean.TRUE/FALSE statics — new)**, **F-050e (registry invariant law — new)** — evidence links in `docs/ROOT_IMPACT_MATRIX.md` |
| **CURRENT FRONTIER** | Job-active cancellation of the Compose frame await (the Recomposer's withFrameNanos continuation is cancelled via its invokeOnCancellation handler before the pump fires) — root-located, PENDING (M9) |
| **TicTacToe (real APK)** | rc=0 SUCCESS, 3-run byte-identical — libGDX GLSurfaceView boundary (T3/BLANK, unchanged historical record) |
| **Telegram** | BLOCKED — official dl serves a 1.2 MB stub installer; the pinned 82 MB v10.14.5 artifact (`193ad551…`) is no longer reachable; fetch correctly rejects (zero-skip law) |
| **IMPACT (M8)** | 4 blocker layers peeled in the dooz first-frame chain: scheduler state corruption (getAndIncrement decrement bug) → ISE "unexpected close status: -1" → channel-cancel cascade (Boolean.TRUE null) → frame callback never fired (Choreographer family) — all four fixed, micro-proven 7/7 bands + 3-run byte-identical |
| **KNOWN LIMITATIONS** | dooz framebuffer still 0 non-white (deterministic BLANK, SHA `31ddd4d5…`); Compose tap→recompose unproven; WeakReference + DecorView content-hierarchy roots open |

**DOOZ HAS ADVANCED THROUGH THE RECOMPOSER / FRAME-CLOCK MACHINERY
(Choreographer family landed, four scheduler-corruption roots closed),
BUT THE FINAL COMPOSE FRAME IS STILL NOT PROVEN/RENDERED.**

Do NOT claim Compose success from this README — the framebuffer is blank
and the statement above is the current verified truth.

---

## What is MiniAndroid?

A from-scratch C++17 runtime that:

1. parses real APK files (ZIP + `resources.arsc` + binary XML + DEX),
2. interprets real Dalvik bytecode with tagged-value semantics,
3. resolves real resources and inflates real view trees,
4. dispatches the real Android lifecycle and input pipeline,
5. renders to a software framebuffer with pixel-evidence output
   (screenshots + per-frame SHA256 + deterministic replay).

### What it is NOT

- **Not** an emulator or a JVM/ART fork — the DEX interpreter, resource
  stack, and framework shadows are all first-party C++.
- **Not** a GUI product — it is a compatibility runtime and evidence engine.
- **Not** claimed complete: every capability row below names its evidence,
  and every known gap is listed, not hidden.

## Architecture / execution pipeline

```text
APK ZIP
 → Manifest (AXML) → PackageManager/activity registration
 → resources.arsc (string pools, packages, configs) + res/ drawables
 → classes(.N).dex → class_data delta chains → method/field resolution
 → Dalvik interpreter (tagged registers, per-opcode laws)
 → framework shadows (Context/Activity/View/Handler/… service registry)
 → lifecycle (onCreate → onStart → onResume) → view tree
 → measure/layout → software Canvas render → framebuffer PNG + SHA256
 → input: click/tap dispatch through the app's own DEX handlers
 → deterministic virtual-time Looper (3-run byte-identical law)
```

## What is now proven (evidence-backed at this commit)

### Headline: real-APK execution proof with visible state transitions

A dedicated, fully open-source demo app (`demo/`, MIT) is built with the
official Android toolchain components (ECJ + AOSP D8 + Google's API-34
`android.jar`) and executed end-to-end: a click dispatches through DEX
bytecode and changes EVERY visible state dimension at once — counter,
position, color, status text — with per-frame SHA256 evidence and a
deterministic replay check (8 clicks, 9 frames, all hashes distinct,
3-run replay byte-identical).
Evidence: [docs/demo/EVIDENCE.md](docs/demo/EVIDENCE.md),
[docs/demo/demo_proof.gif](docs/demo/demo_proof.gif).

### The golden fixture: interactive Tic-Tac-Toe

`9/9 clicks dispatched · turn alternation · X WINS · glyph ink localized
per cell · frames 7/8/9 byte-identical (frozen game) · 10-frame replay
byte-identical across independent runs` — battery stage §29.

### Real-APK corpus (SHA-verified)

| APK | Status |
|---|---|
| HelloWorld (self-aware) | renders, 99% non-white, EXT goldens |
| tictactoe_golden (fixture APK) | 9/9 clicks, X WINS, deterministic |
| microtimer | renders (50% non-white), F-012 persistence PASS |
| simplestopwatch | renders (110k px), interaction-driven state |
| gmdice | renders (84% non-white), menu/roll state flips |
| chessclock | per-panel timers via postDelayed + virtual clock, 3-run byte-identical |
| unote | XML onClick handlers fire on the hosting Activity |
| **dooz (Compose lighthouse)** | **execution frontier advanced — see below** |

### Compose status (F-044 era — nothing overstated)

- Compose attach executes: `setContent → ComposeView → AndroidComposeView
  → onAttachedToWindow` runs to its LAST DEX instruction; the derived-state
  machinery (Snapshot/MutableState/DerivedSnapshotState version hashes,
  dependency tables) executes as real DEX.
- The runtime now correctly executes the Compose **derived-state
  dependency-change law** (F-044): version hashes keep their full 32-bit
  values, so a state write invalidates a derived read — pre-F-044 every
  such hash collapsed to a boolean and derived state was permanently stale.
- `System.identityHashCode` follows the OpenJDK identity law (F-045) —
  previously a silent fail-soft 0-for-everything.
- **NOT yet proven: a visible Compose frame.** The remaining blocker is the
  first-frame pump (Recomposer frame → measure/layout/draw through the
  AndroidUiDispatcher/MonotonicFrameClock delayed dispatch) — root-located,
  documented, PENDING. dooz's framebuffer is still blank and we say so.

### Root-law ledger

Every fix is a **semantic law** (no app special-casing, ever), upstream-
evidenced against AOSP/ART/OpenJDK/AndroidX, micro-proven with a real
ECJ+D8 DEX fixture, and regression-gated by the battery:
[docs/ROOT_LAW_GLOBAL_AUDIT.md](docs/ROOT_LAW_GLOBAL_AUDIT.md) (full ledger
with per-root impact columns),
[docs/ROOT_LAW_COMPLETENESS_MATRIX.md](docs/ROOT_LAW_COMPLETENESS_MATRIX.md)
(family closure status — root complete ≠ family closed),
[docs/ROOT_LAW_IMPACT_REPORT.md](docs/ROOT_LAW_IMPACT_REPORT.md) (what
actually improved, with before/after),
[docs/ROOT_DISCOVERY_GUIDE.md](docs/ROOT_DISCOVERY_GUIDE.md) +
[docs/ROOT_DISCOVERY_EVIDENCE.md](docs/ROOT_DISCOVERY_EVIDENCE.md) (how a
failure becomes a root candidate — the F-044 worked example).

## Determinism — how to reproduce

```bash
make clean && make -j
bash scripts/run_test_battery.sh        # → "BATTERY GATE: ALL PASS (88 stages)"
./miniandroid/build/miniandroid run <apk> -o run/out
# every run: screenshot.png + screenshot.ppm + report.md + crash.log
# 3-run law: byte-identical framebuffer SHA256 across independent runs
```

## Quick start (release artifact)

```bash
tar xzf MiniAndroid-v0.0.3-*-linux-x64.tar.gz && cd miniandroid-0.0.3
./miniandroid run demo.apk -o run/demo
# → proof/frames/*.png + proof/frames/manifest.json (per-frame SHA256)
```

## Release provenance (v0.0.3 policy)

`source commit == tag commit == binary build commit`. The exact source
commit, tag, binary, artifact SHA256s and release notes form one traceable
chain — see [docs/RELEASE_v0.0.3.md](docs/RELEASE_v0.0.3.md) and the
`SHA256SUMS_v0.0.3.txt` asset. (Earlier releases' tag/build skew is
documented in their notes; v0.0.3 closes that gap.)

## Known Limitations (real, current — nothing hidden)

1. **Compose final UI**: no visible Compose frame yet — the first-frame
   pump (delayed dispatch through the frame clock) is the documented next
   battle. dooz renders a deterministic BLANK frame and we claim nothing
   more.
2. **GLES dispatch hook** (K-25): PortableGL glue exists (standalone golden
   cube renders) but the GLSurfaceView/EGL loop is not wired into the
   engine.
3. **Layout geometry**: weight distribution wrong (simplestopwatch buttons
   render full-height).
4. **Fonts**: BitmapFont long-string overlap (SFS-010); the
   FreeType+HarfBuzz+FriBidi RTL pipeline is a proven POC (6/6 Persian
   samples), not yet the TextView path.
5. **Telegram golden APK** (K-26): exact build lost from external cache;
   upstream serves newer bytes → baseline not re-assertable until
   re-acquired. simplestopwatch carries the pixel-exact regression proof.
6. **Canvas matrix composition**: dispatch presence verified; exhaustive
   rotate+scale+clip interplay tests still missing.
7. **Obfuscated AXML** (`res/0s.xml`-style trees): abort safely (guarded),
   not inflated.
8. **JNI/ELF**: boundary classification only; no loader (no corpus APK
   currently demands it; missing native libs are never reported as Java
   blockers).

## Methodology — how this project defines PROVEN

`APK execution → actual view/layout/draw operations → real software
framebuffer → screenshot artifact → SHA256 + non-white count + 3-run
reproducibility`. A synthetic screenshot, an rc=0, or a method count is
NOT evidence. `PROVEN / IMPROVED / REMAINING BOUNDARY` are reported as
three separate levels in every release.

## Roadmap

1. Compose first-frame pump (the scheduler/delayed-dispatch law) → the
   first non-blank Compose frame, pixel-proven.
2. Compose interaction (tap → recompose → re-render).
3. System-service family completion (F-046 candidates).
4. Measure/weight edge semantics quantified against a weights-heavy APK.
5. Independent Compose APK (a second Compose app, not dooz).

Historical context and the full fix ledger:
[MASTER_PROJECT_KNOWLEDGE.md](MASTER_PROJECT_KNOWLEDGE.md),
[NOT_DONE.md](NOT_DONE.md), [START_HERE.md](START_HERE.md).

---

**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
· **License:** MIT · Every claim on this page is re-verified at each push
by the 88-stage battery.
