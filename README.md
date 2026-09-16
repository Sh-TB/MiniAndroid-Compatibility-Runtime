# MiniAndroid — a from-scratch Android APK Compatibility Runtime

<p align="center">
  <img src="docs/assets/miniandroid-silkie-mascot.png" width="132" alt="MiniAndroid mascot — a fluffy Silkie hen (decorative only)">
</p>
<p align="center"><sub>Decorative project mascot — a Silkie hen. Not an Android/Google mark; carries no claim.</sub></p>

**Current Release:** `v0.0.6 — Leghorn` (repository recovery + battery restoration 94/94 + evidence compaction, 2026-09-16)
**Previous:** `v0.0.5 — Silkie` (Hello Color real-APK milestone) · `v0.0.4-Chantecler` (Choreographer frame-pump family F-050) · `v0.0.3 — Chantecler` (Compose frontier + root-law closure) · `v0.0.2 — Australorp` (real-APK execution proof) · `v0.0.1 — Brahma`
**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime (original project, not a fork)
**License:** MIT

---

## What is MiniAndroid?

A from-scratch C++17 runtime that:

1. parses real APK files (ZIP + `resources.arsc` + binary XML + DEX),
2. interprets real Dalvik bytecode with tagged-value semantics,
3. resolves real resources and inflates real view trees,
4. dispatches the real Android lifecycle and input pipeline,
5. renders to a software framebuffer with pixel-evidence output
   (screenshots + per-frame SHA256 + deterministic replay).

**What it is NOT**

- **Not** an emulator or a JVM/ART fork — the DEX interpreter, resource
  stack, and framework shadows are all first-party C++.
- **Not** a GUI product — it is a compatibility runtime and evidence engine.
- **Not** claimed complete: every capability row below names its evidence,
  and every known gap is listed, not hidden.

## Why it exists

Android compatibility is usually asserted ("it runs"), rarely proven. MiniAndroid
is built around a different rule: **a claim exists only if a committed,
machine-checkable artifact backs it.** Every fix is a generic semantic law
(upstream-evidenced against AOSP/ART/OpenJDK/AndroidX, never app-special-cased),
every capability is pinned to a framebuffer SHA256, and every known gap is
registered — not hidden. The project doubles as an evidence engine: if the
runtime cannot honestly render it, the registry says so.

## Verified real-APK execution (screenshot)

<p align="center">
  <img src="docs/assets/hello_color_readme_540.png" width="330" alt="Hello Color frame rendered by MiniAndroid's own runtime from a real APK">
</p>

**Hello Color is verified as a real APK execution and rendering path.** The image
above is the runtime's own framebuffer capture — not a mockup, not a reference
image, not a golden used as input. Provenance chain (forensically verified,
three-run deterministic):

```text
Source → APK (77863f1f…) → DEX → MiniAndroid Dalvik interpreter
      → Android Activity/View calls → framebuffer (PPM fb9f1df2…)
      → PNG (11e00563…) — pixel-identical across 3 independent runs
```

Full forensic record: [`docs/evidence/hello_color_golden/PROVENANCE_FORENSIC.json`](docs/evidence/hello_color_golden/PROVENANCE_FORENSIC.json)
(execution traces, opcode-level `REAL_DALVIK_INTERPRETER` evidence, framebuffer↔PNG
byte identity, golden-never-input proof). Image transform + SHA relation:
[`docs/assets/DERIVED_IMAGE_PROVENANCE.json`](docs/assets/DERIVED_IMAGE_PROVENANCE.json).
The interactive demo app (box moving on a 5×4 grid via real DEX click handlers):
[`docs/demos/EVIDENCE.md`](docs/demos/EVIDENCE.md) · [`docs/demos/demo_proof.gif`](docs/demos/demo_proof.gif).

## Current verified capabilities

Only what the committed evidence supports — each item is machine-checkable at
this tag. Full detail: [`docs/releases/RELEASE_v0.0.6-Leghorn.md`](docs/releases/RELEASE_v0.0.6-Leghorn.md)
and [`docs/testing/BATTERY_INDEX.json`](docs/testing/BATTERY_INDEX.json).

1. **Real DEX interpreter + real resource stack + real rendering** — a real
   aapt2+ECJ+D8-built APK (`77863f1f…`) executes through the first-party DEX
   interpreter and renders through the first-party software renderer; three
   independent runs are byte-identical (`PROVENANCE_FORENSIC.json`).
2. **TicTacToe Classic (real corpus APK) is fully playable** — real taps →
   DEX click listeners → X/O alternation → board redraws (S44); the §29
   interaction + determinism golden passes with 10-frame per-frame SHAs.
3. **Regression battery: 94/94 ALL PASS** — §28 HelloWorld (26 checks), §29
   TicTacToe (8 checks), EXT-01 typography 9/9, EXT-02 interaction 12/12,
   G06/G07/G08 3-run frame-SHA determinism, all fixture pixel goldens
   (`docs/testing/BATTERY_INDEX.json`).
4. **Real Android lifecycle/input/persistence dispatch** — Activity
   onCreate→onStart→onResume, click dispatch through app DEX handlers,
   SharedPreferences/SQLite-backed persistence paths (package-dir law
   R-NEW-367 VERIFIED-FIXED).
5. **Real corpus APKs render** — ChessClock deterministic screenshot
   (`e4a2d7c9…` ×3), gmdice/microtimer/unote byte-stable frames; corpus
   grades in `docs/compatibility/` and the APPS_EXECUTION_LEDGER.
6. **REAL TELEGRAM v12.10.1 executed (frontier)** — the official 73 MB APK
   (`f5e11927…`) parses, LAUNCHES, paints a themed frame; deeper init stops
   at the desugared-streams gap (**R-NEW-303**, honestly open).
7. **Current frontier: R-NEW-361** — dooz v18/v23 converge on the compose
   SlotTable/ScatterMap probe-arithmetic face (refined R-NEW-335). Forensics
   recorded; NOT fixed yet. dooz has no visible frame yet — claimed nothing
   beyond the evidence. 2048 executes via the corpus path and is NOT claimed
   playable.

## Architecture summary

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

Deeper documents: [`docs/architecture/`](docs/architecture/),
[`docs/runtime/architecture.md`](docs/runtime/architecture.md).

## Quick start

Build from source:

```bash
make -C miniandroid clean && make -C miniandroid -j
./miniandroid/build/miniandroid run <apk> -o run/out
# every run: screenshot.png + screenshot.ppm + report.md + crash.log
```

Or use a release artifact:

```bash
tar xzf MiniAndroid-v0.0.3-*-linux-x64.tar.gz && cd miniandroid-0.0.3
./miniandroid run demo.apk -o run/demo
# → proof/frames/*.png + proof/frames/manifest.json (per-frame SHA256)
```

## Verification & evidence

```bash
bash scripts/test/run_test_battery.sh   # full regression battery → "BATTERY GATE: ALL PASS (94 stages)"
```

- **Methodology:** `APK execution → actual view/layout/draw operations → real
  software framebuffer → screenshot artifact → SHA256 + non-white count +
  3-run reproducibility`. A synthetic screenshot, an rc=0, or a method count is
  NOT evidence.
- **Battery inventory:** [`docs/testing/BATTERY_INDEX.json`](docs/testing/BATTERY_INDEX.json)
  — machine-readable list of all 94 stages and their last verified status.
- **Upstream law ledger:** [`docs/upstream/INDEX.md`](docs/upstream/INDEX.md)
  (the semantic contract each fix implements),
  [`docs/research/ROOT_LAW_GLOBAL_AUDIT.md`](docs/research/ROOT_LAW_GLOBAL_AUDIT.md)
  (full ledger), [`docs/research/ROOT_IMPACT_MATRIX.md`](docs/research/ROOT_IMPACT_MATRIX.md)
  (per-root impact).
- **Registry:** [`root_registry.json`](root_registry.json) — one honest record per
  root (348 entries, P0–P3, canonical status vocabulary).
- **Evidence tree:** [`docs/evidence/`](docs/evidence/) — compact, machine-verifiable
  provenance per case; raw campaign exhaust is archived externally with SHA-256
  provenance in [`docs/evidence/ARCHIVE_MANIFEST.json`](docs/evidence/ARCHIVE_MANIFEST.json)
  and can never re-enter the tree (`.gitignore`-enforced).

## Current limitations (real, current — nothing hidden)

1. **Compose final UI**: no visible Compose frame yet for dooz — **R-NEW-361**
   (refined R-NEW-335) is the primary frontier: both dooz variants converge on
   androidx ScatterMap probe arithmetic producing negative indices (HALT-LOOP
   → aput-oob). Forensics recorded in `docs/maintenance/s45_session_record.md`;
   not fixed.
2. **Telegram frontier**: **R-NEW-303** (desugared-streams builder dispatch) —
   honestly open, evidence committed.
3. **2048** executes on the corpus path and renders partially; **not claimed
   playable** until real UI/gameplay is verified with input evidence.
4. **GLES dispatch hook** (K-25): PortableGL glue exists (standalone golden cube
   renders) but the GLSurfaceView/EGL loop is not wired into the engine.
5. **Layout geometry**: weight distribution wrong (simplestopwatch buttons render
   full-height); headingcalc display-row text overlap (open visual gap).
6. **Fonts**: BitmapFont long-string overlap (SFS-010); the GATE H
   glyph-to-framebuffer gap; the FreeType+HarfBuzz+FriBidi RTL pipeline is a
   proven POC (6/6 Persian samples), not yet the TextView path.
7. **Corpus gaps**: kiss AppCompat theme resolution; openlauncher Fragment-host
   attach; bgclock WebViewAssetLoader builder; stopwatch2 androidx init.
8. **Canvas matrix composition**: dispatch presence verified; exhaustive
   rotate+scale+clip interplay tests still missing.
9. **Obfuscated AXML** (`res/0s.xml`-style trees): abort safely (guarded), not
   inflated.
10. **JNI/ELF**: boundary classification only; no loader (no corpus APK currently
    demands it; missing native libs are never reported as Java blockers).

## Documentation

The complete documentation index lives in **[`docs/INDEX.md`](docs/INDEX.md)**
(machine-readable twin: `docs/INDEX.json`) — architecture, testing, runtime,
dex, resources, lifecycle, rendering, input, persistence, upstream laws,
releases, forensic evidence, maintenance, and history.

## Release

`source commit == tag commit == binary build commit` — the exact source commit,
tag, binary, artifact SHA256s and release notes form one traceable chain. See
[`docs/releases/`](docs/releases/) and the per-release `SHA256SUMS_*.txt` asset.
Current: **`v0.0.6 — Leghorn`** · notes:
[`docs/releases/RELEASE_v0.0.6-Leghorn.md`](docs/releases/RELEASE_v0.0.6-Leghorn.md)
· manifest: [`docs/releases/RELEASE_MANIFEST.json`](docs/releases/RELEASE_MANIFEST.json).
Windows packaging is lean by law: only the runtime binary, the first-party demo
APK, README and LICENSE — enforced by `scripts/release/check_release_artifacts.sh`.

---

**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
· **License:** MIT · Every claim on this page is re-verified at each push by the
regression battery ([`scripts/test/run_test_battery.sh`](scripts/test/run_test_battery.sh)).
