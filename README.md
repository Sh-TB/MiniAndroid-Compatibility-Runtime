# MiniAndroid — a from-scratch Android APK Compatibility Runtime

<p align="center">
  <img src="docs/assets/miniandroid-silkie-mascot.png" width="132" alt="MiniAndroid mascot — a fluffy Silkie hen (decorative only)">
</p>
<p align="center"><sub>Decorative project mascot — a Silkie hen. Not an Android/Google mark; carries no claim.</sub></p>

**Current Release:** `v0.0.5 — Silkie` (Hello Color real-APK execution milestone, 2026-09-12)
**Previous:** `v0.0.4-Chantecler` (Choreographer frame-pump family F-050) · `v0.0.3 — Chantecler` (Compose frontier + root-law closure) · `v0.0.2 — Australorp` (real-APK execution proof) · `v0.0.1 — Brahma`
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
this tag. Full detail: [`docs/releases/STATUS_MC4_2026-09-12.md`](docs/releases/STATUS_MC4_2026-09-12.md).

1. **REAL APK EXECUTION + REAL RUNTIME RENDERING (Hello Color)** — a real
   aapt2+ECJ+D8-built APK (`77863f1f…`) executes through the first-party DEX
   interpreter and renders through the first-party software renderer
   (`PROVENANCE_FORENSIC.json`); re-verified byte-identical (`11e00563…`) on the
   R-NEW-302-fixed binary.
2. **Deterministic rendering** — three independent runs produce the byte-identical
   framebuffer (PPM `fb9f1df2…` ×3, PNG `11e00563…` ×3).
3. **Real DEX interpreter execution** — opcode-level trace with pc/opcode/return
   values and `execution_source=REAL_DALVIK_INTERPRETER`.
4. **Real Android resource loading** — `setContentView` dispatches with a real
   resource ID (`2130903040`) resolved from a real binary `resources.arsc`.
5. **Real View interaction from app bytecode** — `setBackgroundColor`,
   `setTextColor` ×3, `findViewById` ×4 (real heap objects) invoked by the app's
   own DEX, not by the host.
6. **HelloWorld + TicTacToe golden batteries** — §28 (26 checks) and §29
   (interaction + determinism, X→O→X WINS across a 10-frame golden) PASS;
   3-run byte-identical (`docs/evidence/tictactoe_golden/`, `docs/evidence/helloworld_golden/`).
7. **ChessClock (real corpus APK)** — rc=0 ×3 with a deterministic framebuffer
   screenshot (1080×1920, SHA `e4a2d7c9…` ×3 byte-identical;
   `docs/evidence/campaign3_chessclock_real_screenshot/`).
8. **R-NEW-302 FIXED (MC4 self-improvement)** — the demo box MOVES on its declared
   5×4 grid: AOSP FrameLayout margins+gravity law, root MATCH_PARENT window law,
   and the requestLayout re-measure law landed as one generic pass;
   `examples/demo-app/validate_demo_proof.sh` → VALIDATION_PASS, zero regressions.
9. **REAL TELEGRAM v12.10.1 executed (frontier)** — the official 73 MB
   `org.telegram.messenger.web` APK (sha256 `f5e11927…`) parses, LAUNCHES, and
   paints one full-screen themed frame; deeper init stops at the desugared-streams
   gap (**R-NEW-303**, honestly open). Evidence: `docs/evidence/mc4_telegram/`.
   NOT claimed usable.
10. **MC4 corpus sweep (13 real APKs, standard path, zero flags)** — 8 exit rc=0
    with real rendered frames (gmdice 1.74M px, simplestopwatch 1.94M px,
    headingcalc 2.05M px keypad, microtimer 1.04M px, unote UI chrome; dooz /
    tictactoe_gdx / simplekeyboard blank at known GL/Compose/IME boundaries);
    5 exit rc=1 with honestly-classified causes.

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
bash scripts/test/run_test_battery.sh   # full regression battery → "BATTERY GATE: ALL PASS"
```

- **Methodology:** `APK execution → actual view/layout/draw operations → real
  software framebuffer → screenshot artifact → SHA256 + non-white count +
  3-run reproducibility`. A synthetic screenshot, an rc=0, or a method count is
  NOT evidence. `PROVEN / IMPROVED / REMAINING BOUNDARY` are reported as three
  separate levels in every release.
- **Root-law ledger:** [`docs/research/ROOT_LAW_GLOBAL_AUDIT.md`](docs/research/ROOT_LAW_GLOBAL_AUDIT.md)
  (full ledger), [`docs/research/ROOT_IMPACT_MATRIX.md`](docs/research/ROOT_IMPACT_MATRIX.md)
  (per-root impact), [`docs/research/ROOT_DISCOVERY_GUIDE.md`](docs/research/ROOT_DISCOVERY_GUIDE.md)
  (how a failure becomes a root candidate).
- **Registry:** [`root_registry.json`](root_registry.json) — one honest record per
  root (F-xxx / R-NEW-xxx, P0–P3, OBSERVED-FAIL / IMPLEMENTED / VERIFIED-FIXED).
- **Evidence tree:** [`docs/evidence/`](docs/evidence/) — machine-verifiable
  provenance per case (hello_color_golden, tictactoe_golden, mc4_telegram, …).

## Current limitations (real, current — nothing hidden)

1. **Compose final UI**: no visible Compose frame yet — **F-077** (initial
   composition hits a kotlinx TrieNode invariant NPE) is the one remaining break
   before the first frame request. dooz renders a deterministic BLANK frame and
   we claim nothing more.
2. **Telegram frontier**: **R-NEW-303** (desugared-streams builder dispatch) —
   honestly open, evidence committed.
3. **GLES dispatch hook** (K-25): PortableGL glue exists (standalone golden cube
   renders) but the GLSurfaceView/EGL loop is not wired into the engine.
4. **Layout geometry**: weight distribution wrong (simplestopwatch buttons render
   full-height); headingcalc display-row text overlap (open visual gap).
5. **Fonts**: BitmapFont long-string overlap (SFS-010); the GATE H
   glyph-to-framebuffer gap; the FreeType+HarfBuzz+FriBidi RTL pipeline is a
   proven POC (6/6 Persian samples), not yet the TextView path.
6. **Corpus gaps**: kiss AppCompat theme resolution; openlauncher Fragment-host
   attach; bgclock WebViewAssetLoader builder; stopwatch2 androidx init.
7. **Canvas matrix composition**: dispatch presence verified; exhaustive
   rotate+scale+clip interplay tests still missing.
8. **Obfuscated AXML** (`res/0s.xml`-style trees): abort safely (guarded), not
   inflated.
9. **JNI/ELF**: boundary classification only; no loader (no corpus APK currently
   demands it; missing native libs are never reported as Java blockers).

## Documentation

The complete documentation index lives in **[`docs/README.md`](docs/README.md)** —
architecture, development, build, testing, compatibility, research, evidence,
demos, releases, decisions, maintenance, and history.

## Release

`source commit == tag commit == binary build commit` — the exact source commit,
tag, binary, artifact SHA256s and release notes form one traceable chain. See
[`docs/releases/`](docs/releases/) and the per-release `SHA256SUMS_*.txt` asset.
Current: **`v0.0.5 — Silkie`** · notes:
[`docs/releases/RELEASE_v0.0.5-Silkie.md`](docs/releases/RELEASE_v0.0.5-Silkie.md).

---

**Repository:** https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
· **License:** MIT · Every claim on this page is re-verified at each push by the
regression battery ([`scripts/test/run_test_battery.sh`](scripts/test/run_test_battery.sh)).
