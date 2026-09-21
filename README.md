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

## At a glance (30 seconds)

- **What it is:** a from-scratch C++17 compatibility runtime that executes real Android APKs from bytecode to pixels, with every claim pinned to committed evidence.
- **What really runs today (S55):** **6 real F-Droid APKs render recognizable full GUI** (Chess Clock, GM Dice, MicroTimer, Simple Stopwatch, Heading Calculator, uNote) — **6 of them with input→state-change screenshot pairs**. GM Dice renders the app-specific result (real dice roll `14 · 15 · 15`); Chess Clock renders the real two-panel clock face and switches the active player on tap (S54 restored it via F-080/F-081); **Notes joined at S55 (F-082)** — the ViewSwitcher read↔edit state machine works (FAB click → 2.06M px face swap); its note-CONTENT face stays blank-class because it is a WebView subclass (generic WebView content model = pinned next dependency).
- **HelloWorld is the proven control target:** the real external HelloWorldSelfAware APK (SHA-verified `009b4671…`) executes end-to-end — typography golden 9/9 vs the upstream phone screenshot + interaction 12/12 + committed framebuffer image.
- **Honesty gate:** the screenshot quality gate (luminance/color/entropy + click-test audit) has downgraded and re-verified claims multiple times — Chess Clock and Notes were recorded `RENDER_ONLY` at S53; Chess Clock was **upgraded back on evidence** (F-080+F-081) at S54; **Notes was upgraded to L7 mode-switch at S55 (F-082)** while its content face remains honestly blank-class (R-NEW-377: MarkdownView extends WebView). No white/black frame is ever presented as an achievement.
- **Dooz:** v23 executes the full Hilt/DI/Compose pipeline deterministically but the first frame is still blank (**R-NEW-344**); v18's ScatterMap probe spin was **ROOT-CAUSED + FIXED at S55 (F-083: depth-cap frame drops corrupted metadata init)** — MainActivity.onStart/onResume now dispatch for the first time; the new pinned frontier is **R-NEW-376** (post-F-083 ctor-climb budget).
- **Telegram v12:** parses + launches + burns 540 s inside real init (no frame yet); startup path fully mapped by ASC recon.
- **Battery:** "BATTERY GATE: ALL PASS (96 stages)" at the current HEAD (`scripts/test/run_test_battery.sh`; 92 stages when the external EXT fixture is absent — documented count law).
- **Full per-app truth:** [**Achievements & Evidence**](docs/ACHIEVEMENTS.md) — the single canonical record of every real APK execution · gate-passing screenshots: [`docs/evidence/s54_frames/`](docs/evidence/s54_frames).

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
2. **TicTacToe is fully playable at the fixture gate** — real taps →
   DEX click listeners → X/O alternation → win state → board redraws
   (tictactoe_golden, §29 interaction + determinism with 10-frame per-frame
   SHAs). The real corpus game gate is additionally held by GM Dice and
   Chess Clock (L7 chains with committed screenshot pairs). The historical
   "TicTacToe Classic (palahsu) fully playable" record stands at its
   recorded HEAD; that APK is currently unavailable (BLOCKED, S54).
3. **Regression battery: "ALL PASS (96 stages)"** — §28 HelloWorld (18 checks),
   §29 TicTacToe interaction 9/9, EXT-01 typography 9/9, EXT-02 interaction
   12/12, G06/G07/G08 3-run frame-SHA determinism, all fixture pixel goldens
   (`docs/testing/BATTERY_INDEX.json`; 92 stages when the external EXT fixture
   is absent — the two EXT run gates collapse; count law documented).
4. **Real Android lifecycle/input/persistence dispatch** — Activity
   onCreate→onStart→onResume, click dispatch through app DEX handlers,
   SharedPreferences/SQLite-backed persistence paths (package-dir law
   R-NEW-367 VERIFIED-FIXED).
5. **Real corpus APKs render** — **6 apps with recognizable GUI**: Chess Clock
   (real clock face, active-player switch on tap — S54), GM Dice (dice-roll
   result rendered), MicroTimer (`00:00:00` display), Simple Stopwatch
   (Start→Stop/Lap), Heading Calculator (keypad+display), uNote (list UI);
   per-app ladder + persistence experiments in
   [`docs/ACHIEVEMENTS.md`](docs/ACHIEVEMENTS.md).
6. **REAL TELEGRAM v12.10.1 executed (frontier)** — the official 73 MB APK
   (`f5e11927…`) parses, LAUNCHES, paints a themed frame; deeper init stops
   at the desugared-streams gap (**R-NEW-303**, honestly open).
7. **Current frontier: R-NEW-376 (S55)** — after F-083 fixed the ScatterMap
   face (R-NEW-361 was a depth-cap frame drop corrupting metadata init),
   dooz v18 Compose init now builds constructor chains that exceed the
   2048-frame budget (9 cap-climbs; hop evidence in docs/evidence/s55_dooz/).
   dooz has no visible frame yet — claimed nothing beyond the evidence.
   2048 executes via the corpus path and is NOT claimed playable.

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
bash scripts/test/run_test_battery.sh   # full regression battery → "BATTERY GATE: ALL PASS (96 stages)"
```

- **Methodology:** `APK execution → actual view/layout/draw operations → real
  software framebuffer → screenshot artifact → SHA256 + non-white count +
  3-run reproducibility`. A synthetic screenshot, an rc=0, or a method count is
  NOT evidence.
- **Battery inventory:** [`docs/testing/BATTERY_INDEX.json`](docs/testing/BATTERY_INDEX.json)
  — machine-readable list of all 96 stages and their last verified status.
- **Upstream law ledger:** [`docs/upstream/INDEX.md`](docs/upstream/INDEX.md)
  (the semantic contract each fix implements),
  [`docs/research/ROOT_LAW_GLOBAL_AUDIT.md`](docs/research/ROOT_LAW_GLOBAL_AUDIT.md)
  (full ledger), [`docs/research/ROOT_IMPACT_MATRIX.md`](docs/research/ROOT_IMPACT_MATRIX.md)
  (per-root impact).
- **Registry:** [`root_registry.json`](root_registry.json) — one honest record per
  root (349 entries, P0–P3, canonical status vocabulary).
- **Evidence tree:** [`docs/evidence/`](docs/evidence/) — compact, machine-verifiable
  provenance per case; raw campaign exhaust is archived externally with SHA-256
  provenance in [`docs/evidence/ARCHIVE_MANIFEST.json`](docs/evidence/ARCHIVE_MANIFEST.json)
  and can never re-enter the tree (`.gitignore`-enforced).

## Current limitations (real, current — nothing hidden)

1. **Compose final UI**: no visible Compose frame yet for dooz — **R-NEW-344**
   (Recomposer suspension; blank frame class `31ddd4d5…`) and **R-NEW-376**
   (post-F-083 ctor-climb frontier; S55 pinned with hop traces). The S53-era
   **R-NEW-361** face is VERIFIED-FIXED by **F-083** (ART-sized engine stack +
   loud limit-drop; evidence in `docs/evidence/s55_dooz/`). Forensics
   recorded; not fixed.
2. **Telegram frontier**: 540 s inside real init (REC-MISS static-init surface,
   SafeIterableMap cycle-stub ≥18k calls); **R-NEW-303** (desugared-streams)
   stands at its recorded HEAD — honestly open, evidence committed.
3. **uNote input**: buttons render but no tap target is hit-testable anywhere
   (**R-NEW-368**, NEW S52) — paint vs touch geometry divergence.
4. **Persistence**: storage round-trip VERIFIED for chessclock/unote
   (`--data-root` experiment); full state-delta ladder pending R-NEW-368 +
   interactive drivers.
5. **2048** executes on the corpus path and renders partially; **not claimed
   playable** until real UI/gameplay is verified with input evidence.
6. **GLES dispatch hook** (K-25): PortableGL glue exists (standalone golden cube
   renders) but the GLSurfaceView/EGL loop is not wired into the engine.
7. **Layout geometry**: weight distribution wrong (simplestopwatch buttons render
   full-height); headingcalc display-row text overlap (open visual gap).
8. **Fonts**: BitmapFont long-string overlap (SFS-010); the GATE H
   glyph-to-framebuffer gap; the FreeType+HarfBuzz+FriBidi RTL pipeline is a
   proven POC (6/6 Persian samples), not yet the TextView path.
9. **Corpus gaps**: kiss AppCompat theme resolution; openlauncher Fragment-host
   attach; bgclock WebViewAssetLoader builder; stopwatch2 androidx init.
10. **Canvas matrix composition**: dispatch presence verified; exhaustive
    rotate+scale+clip interplay tests still missing.
11. **Obfuscated AXML** (`res/0s.xml`-style trees): abort safely (guarded), not
    inflated.
12. **JNI/ELF**: boundary classification only; no loader (no corpus APK currently
    demands it; missing native libs are never reported as Java blockers).

## Documentation

Canonical files — one per role:

- **[Achievements & Evidence](docs/ACHIEVEMENTS.md)** —
  the single source of truth for every real APK execution: per-app ladder,
  persistence experiments, screenshots (SHA256, ≤100 KB JPG, real UI only),
  ASC reconnaissance ledger. Curated gallery: [`docs/evidence/s54_frames/`](docs/evidence/s54_frames/).
- **[Knowledge Index](docs/KNOWLEDGE_INDEX.md)** — canonical inventory of all
  knowledge/research files (per-file classification + pipeline knowledge map).
- **[Roadmap Status](docs/ROADMAP_STATUS.md)** — the reconciled canonical
  roadmap (all historical roadmaps folded in; P0 frontier ranked).
- **[Compatibility Platform](docs/compatibility/README.md)** (S74) — the
  operational memory: per-app compatibility dossiers (`apps/*.json`),
  tool/source profiles (`tools/*.json`), capability records
  (`capabilities/*.json`), canonical knowledge records
  (`docs/knowledge/laws/*.json`), and the evidence-backed
  [Capability Matrix](docs/compatibility/CAPABILITY_MATRIX.md).
  **Runtime Core is shared; Compatibility Status is app-specific.**
- **[Operational Evidence Bundles](docs/evidence/s74_ops/AUDIT_TABLE.md)**
  (S74 FOLLOW-UP) — per-app human-visible execution evidence
  (`docs/evidence/s74_ops/<app>/`): representative frames (individually
  human-reviewed), session.json execution checkpoints, SHA256SUMS, per-app
  sandbox probes; plus the §27 audit table and the
  [Tool Utilization Matrix](docs/compatibility/TOOL_UTILIZATION.md)
  (USED / RESEARCHED_ONLY / AVAILABLE_NOT_USED, no inflation).
- **[Android Execution Skill](docs/execution-skill/SKILL.md)** (S74) —
  vendor-neutral, token-efficient workflow any coding agent follows to run one
  APK, find its blocker, reuse verified knowledge, fix the runtime, prove the
  result, and update dossier + issue (validated by
  `tools/validate_compatibility_graph.py`; knowledge promotion via
  `tools/promote_knowledge.py`).
- Navigation hub: **[`docs/INDEX.md`](docs/INDEX.md)** (machine-readable twin:
  `docs/INDEX.json`) — architecture, testing, runtime, dex, resources,
  lifecycle, rendering, input, persistence, upstream laws, releases, forensic
  evidence, maintenance, and history.

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
