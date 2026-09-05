# GOLDEN_HELLOWORLD — §13/§28 Permanent Evidence (revalidated)

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Revalidation date: 2026-09-05 · Local HEAD at revalidation: `9e7c0e9b`
(lineage: 738ac50 introduced the golden → docs-only commits → 2c8bf2da
MUTF-8 primitive → 9e7c0e9b WineDroid discriminators; runtime source
identical from 738ac50 through 12947e03, re-built and re-run from clean
at this HEAD)

## §28 required record

| Field | Value |
|---|---|
| Fixture source | `miniandroid/tests/fixtures/helloworld_golden/` (MIT), built by `scripts/build_fixture_apk.sh` (ECJ MIT + D8/r8 Apache-2.0) |
| APK SHA256 (this rebuild) | `bc995efce8827ffce1c3f5446d9be5f9d289900f2b84a7133de64b53d7be1bd4` |
| DEX SHA256 | `702989378d87fb1e193d54db0a607c8f39419cc876070c6671e1f98ec5509756` — **byte-identical to the §28 record at 738ac50** |
| Runtime command | `miniandroid/build/miniandroid run <apk> -o <outdir>` |
| Exit status | 0 (runs A and B) |
| Screenshot | `docs/evidence/helloworld_golden/screenshot.png`, 1080×1920 |
| Screenshot SHA256 | `93b4262188199ce03b196d4115fc389b79a3dd6654cbdca49a30c763b30a01de` — **identical to the record at 738ac50** |
| Determinism | run B byte-identical (cmp) — revalidated twice this campaign (initial + post-FIND-REUSE-001) |

Note on APK-vs-DEX hashing: the APK ZIP embeds timestamps, so its SHA256
varies per packaging run while its DEX payload is deterministic; the §28
determinism oracle is therefore the DEX SHA256 + screenshot SHA256 pair.

## §27 chain exercised (real end-to-end, no bypasses)

APK load → manifest parse → Application → `Activity.onCreate` → class
loading → DEX execution (invoke-virtual dispatch) → View tree
(LinearLayout + 2×TextView + Button) → `setContentView` → real
measure/layout pass → font shaping (FreeType/HarfBuzz/FriBidi) → Canvas
draw → software renderer → visible PNG (1080×1920).

## Validation results (this campaign, both runs)

`validate_helloworld_golden.sh` — **18/18 checks PASS, zero skipped**:
fixture build; APK+DEX hashes; run exit 0; screenshot produced;
EXT-AOSP-001 container `setGravity` intercepted on the real DEX path;
EXT-AOSP-002 `setTextSize` 28sp→73.5px and 14sp→36.75px; pixel band
analysis (28sp band taller than 14sp band; both horizontally centered);
run B byte-identical; SHA/dimensions recorded; zero-skip gate.

## Knowledge-transfer units pinned by this golden

| ID | Mechanism | Provenance | Evidence |
|---|---|---|---|
| EXT-AOSP-001 | Container gravity governs children with no layout_gravity | AOSP frameworks/base @ 1cdfff55, LinearLayout.java L1933-1945/L1284/L1466 | children centered at exactly (1080−w)/2 |
| EXT-AOSP-002 | `setTextSize(float)` == sp × scaledDensity | AOSP TextView.java L4720-4762 | 28sp→73.5px, 14sp→36.75px (density 2.625) |

## Regression state at this HEAD

- tictactoe_golden: ALL PASS (see TICTACTOE_STATUS.md)
- semantic battery: 14 + 57 + 25 = 96/96 PASS (bridge group extended by
  the two WineDroid discriminator cases this campaign)
- MUTF-8 battery: 7/7 PASS (new; FIND-REUSE-001)
- The MUTF-8 primitive change did NOT move any golden pixel (screenshot
  SHA256 unchanged) — the helloworld fixture strings are pure ASCII, and
  the primitive preserves ASCII behavior bit-for-bit.
