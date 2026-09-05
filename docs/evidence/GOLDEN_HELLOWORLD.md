# GOLDEN_HELLOWORLD — §13/§28 Permanent Evidence (resource-backed, §36.E)

Campaign: REUSE-FIRST MAXIMUM PROGRESS / CODE-MINIMIZATION
Upgrade date: 2026-09-05 · Local HEAD at upgrade: `380f654a`
(runtime source unchanged from `9e7c0e9b`; this session changed only the
fixture toolchain + fixture sources + validation gate — the resource
chain was already implemented in the runtime and is now exercised by the
golden instead of remaining corpus-only)

## §28 required record

| Field | Value |
|---|---|
| Fixture source | `miniandroid/tests/fixtures/helloworld_golden/` (MIT), built by `scripts/build_fixture_apk.sh` (aapt2 8.13.2 Apache-2.0 from Google Maven + ECJ MIT + D8/r8 8.3.37 Apache-2.0 + android-34 stubs Apache-2.0) |
| APK SHA256 (deterministic build) | `3cf76fb7b2cb2c02d608966fe97c4644e4abab90b9f3c550e937ffdb827b4d15` |
| DEX SHA256 | `039e18ed62cfd76ee0dda83beb1c0ff16e53b9df207fb85b00f3b26655d3a24f` |
| APK entries | `AndroidManifest.xml` (binary AXML) · `res/layout/activity_main.xml` (binary AXML) · `resources.arsc` · `classes.dex` |
| Runtime command | `miniandroid/build/miniandroid run <apk> -o <outdir>` |
| Exit status | 0 (runs A and B) |
| Screenshot | `docs/evidence/helloworld_golden/screenshot.png` (= `golden_helloworld.png`), 1080×1920 |
| Screenshot SHA256 | `a61f5b224ace9fd7e9ff4e3c50dec44cf5ffa84843cce161e8fc4950cc24ad66` |
| Determinism | run B byte-identical (cmp); APK build itself is byte-deterministic (aapt2 + repackager pin 1980-01-01 zip epochs) |

APK-vs-DEX hashing note: the aapt2 path made BOTH the APK and its
payloads deterministic, so the §28 oracle is now the full triple
APK SHA256 + DEX SHA256 + screenshot SHA256.

## §36.E resource-backed discriminator (NEW — permanent gate)

The §36.E success condition requires a resource-backed Hello World, not
a hard-coded runtime screen. The validation gate now proves this from
the APK bytes themselves:

- all three display strings (`Hello, MiniAndroid!`,
  `real APK - real DEX - real render`, `OK`) are present in
  `resources.arsc` and **ABSENT from `classes.dex`** (string-pool byte
  search, `docs/evidence/helloworld_golden/reschain_report.txt`);
- the layout is aapt2-compiled binary AXML (RES_XML type `0x0003`);
- the manifest is aapt2-compiled binary AXML;
- runtime log shows `[U007-RES] ResourceRuntime loaded … named_ids=8
  types=3` and `[ARSC-VALUES] strings=3` (ARSC-first resolution).

Before this upgrade the fixture hard-coded the strings in Java
(§36.E violation recorded and fixed this session).

## §27 chain exercised (real end-to-end, no bypasses)

APK load → binary manifest parse → Application → `Activity.onCreate` →
class loading → DEX execution → `setContentView(R.layout.activity_main)`
→ binary AXML inflation → `resources.arsc` @string/@id/dimension/color
resolution → View tree (LinearLayout + 2×TextView + Button) →
`findViewById` → DEX-dispatched `setGravity(0x11)` / `setTextSize(28f)`
/ `setTextSize(14f)` / `setText(int)` → real measure/layout pass → font
shaping (FreeType/HarfBuzz/FriBidi) → Canvas draw → software renderer →
visible PNG (1080×1920).

## Validation results (this session)

`validate_helloworld_golden.sh` — **26/26 checks ALL PASS, zero
skipped**: fixture build via aapt2+ECJ+D8; APK/DEX hashes; aapt2-linked
marker; §36.E discriminator ×5 (arsc present, binary layout, AXML magic,
binary manifest, 3× strings-ARSC-not-DEX); run exit 0; screenshot
produced; ResourceRuntime loaded; ARSC-first strings=3; EXT-AOSP-001
gravity law; EXT-AOSP-002 sp law (73.5px + 36.75px); pixel band analysis
(28sp band taller, both centered); run B byte-identical; SHA/dimensions;
zero-skip gate.

Visual note: pixels are visually identical to the previous
programmatic-view golden (same strings/sizes/colors/structure — the
layout XML mirrors the old programmatic tree exactly). Screenshot bytes
changed because the string source (ARSC) and layout path (AXML attrs)
differ, not because the visual result differs.

## Knowledge-transfer units pinned by this golden

| ID | Mechanism | Provenance | Evidence |
|---|---|---|---|
| EXT-AOSP-001 | Container gravity governs children with no layout_gravity | AOSP frameworks/base @ 1cdfff55, LinearLayout.java L1933-1945/L1284/L1466 | children centered at exactly (1080−w)/2 |
| EXT-AOSP-002 | `setTextSize(float)` == sp × scaledDensity | AOSP TextView.java L4720-4762 | 28sp→73.5px, 14sp→36.75px (density 2.625) |
| EXT-AAPT2-001 | aapt2 (Google Maven 8.13.2-14304508) replaces a hand-written binary AXML/ARSC generator — REUSE-FIRST win: zero new format-writer LOC in MiniAndroid | aapt2 Apache-2.0; res zip epoch 1980 determinism observed | APK entries + reschain report |
| EXT-AAPT2-002 | D8 8.3.37 rejects bare class DIRECTORY input; deterministic classes.jar packaging is required | recorded in build_fixture_apk.sh | build log "[3/4] jar entries" |

## FIND recorded this session (not a golden blocker)

- FIND-GRAVITY-VERTICAL: LinearLayout `android:gravity="center"` centers
  children horizontally but the vertical axis still top-aligns (visible
  in BOTH the old programmatic golden and this resource-backed golden;
  AOSP LinearLayout would also center vertically). Queued for the
  Measure/Layout/Draw gate (P0-9); the golden's pixel checks pin only
  horizontal centering, so no gate change.

## Regression state at this HEAD

- tictactoe_golden: ALL PASS (see TICTACTOE_STATUS.md)
- semantic battery: 14 + 57 + 25 = 96/96 PASS
- MUTF-8 battery: 7/7 PASS (FIND-REUSE-001)
- One-command gate: `scripts/run_test_battery.sh` (battery includes this
  golden and rebuilds everything from clean)
