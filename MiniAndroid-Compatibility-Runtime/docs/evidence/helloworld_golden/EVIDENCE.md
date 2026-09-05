# Hello World Golden — §28 Permanent Evidence Record

Campaign: DEEP EXTERNAL REPOSITORY MINING + COMPLETE EXECUTION PUSH
Date: 2026-09-05 · Base HEAD: 5810f6e (before campaign commits)

## Fixture

- Source: `miniandroid/tests/fixtures/helloworld_golden/` (MIT)
- Toolchain: ECJ (MIT) + D8/r8 (Apache-2.0) via `scripts/build_fixture_apk.sh`
- APK SHA256:  `584cda5793fac73e452038ddfc7bb9ccc80984cf322e8871530ea63e16c0f3cd`
- DEX SHA256:  `702989378d87fb1e193d54db0a607c8f39419cc876070c6671e1f98ec5509756`

## §27 chain exercised (real APK → real DEX → real render)

APK load → manifest parse → Application → Activity.onCreate →
class loading → DEX execution (invoke-virtual dispatch) →
View tree construction (LinearLayout + 2×TextView + Button) →
setContentView(View) → real measure/layout pass →
font shaping (FreeType/HarfBuzz/FriBidi) → Canvas draw →
software renderer → visible PNG (1080×1920).

## Knowledge-transfer units validated by this golden

| ID | Mechanism | AOSP provenance (frameworks/base @ 1cdfff55) | Evidence |
|---|---|---|---|
| EXT-AOSP-001 | LinearLayout.setGravity → container gravity governs children with no layout_gravity (`lp.gravity < 0 ? mGravity : lp.gravity`) | LinearLayout.java L1933-1945 (setter), L1284/L1466 (child resolution), L1777-1778 (cross axis) | setGravity(0x11) intercepted; children centered: x=(1080−w)/2 exactly (195/253/513) |
| EXT-AOSP-002 | TextView.setTextSize(float) == setTextSize(COMPLEX_UNIT_SP, size); px = sp × scaledDensity | TextView.java L4720-4722, L4752-4762 (applyDimension→setRawTextSize) | 28sp→73.5px, 14sp→36.75px (density 2.625); headline band measurably taller |

## Runtime evidence

- Command: `miniandroid/build/miniandroid run <apk> -o <outdir>`
- Exit status: 0
- Screenshot: `screenshot.png` (this directory), 1080×1920
- Screenshot SHA256: `93b4262188199ce03b196d4115fc389b79a3dd6654cbdca49a30c763b30a01de`
- Determinism: run B byte-identical (validated by validate_helloworld_golden.sh [4])
- Validation: `validate_helloworld_golden.sh` — 18/18 checks PASS, zero skipped

## Regression state at the commit that introduced this golden

- tictactoe_golden: ALL PASS, frames byte-identical to pre-change baseline
- u011 matrix: 6/7 hashes unchanged; simplestopwatch BASELINE_MATCH
  (pixel-exact law preserved); unote changed 21eb0fd3→df92f1d9 —
  AOSP-correct improvement (container android:gravity now positions
  children; FAB centered, search labels centered in their halves),
  exit code and content unchanged; documented in the campaign final report.
- semantic battery: 14 + 55 + 25 = 94/94 PASS
