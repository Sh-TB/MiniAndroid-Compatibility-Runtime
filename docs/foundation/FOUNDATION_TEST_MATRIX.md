# FOUNDATION_TEST_MATRIX — canonical (S67)

Micro-corpus location: `miniandroid/tests/fixtures_foundation/<name>/`
Builder: `scripts/build/build_fixture_apk.sh` (aapt2+ECJ+D8, byte-deterministic)
Runner: `scripts/foundation/build_run_fixtures.sh`
Verifier: `scripts/foundation/verify_foundation.py` (independent PIL re-decode,
pixel asserts, ViewTree asserts — rc=0/PNG-exists/nonwhite are NOT accepted as proof)
Determinism: `scripts/foundation/determinism_3run.sh`
Evidence: `docs/evidence/foundation/fixtures/<name>/` (screenshot.png, ppm,
view_tree.json, api_trace.json, lifecycle_trace.json, click_test_report.json,
engine.log) + `VERIFICATION.json` + `docs/evidence/foundation/determinism/`

| # (user §17) | Fixture | Base contract | Verdict | Proof artifact |
|---|---|---|---|---|
| R01 | f01_color | solid color bands + px boundaries | PASS 6/6 | f01 VERIFICATION row |
| R03 | f03_alpha | 50% alpha blend (80FF0000 over white) | PASS 4/4 | (255,128,128) exact |
| R04 | f04_text | ASCII TextView render | PASS | text bbox + VT text |
| R05 | f05_persian | Persian shaping via TextView stack | PASS (recorded) | 24218 ink px; joined-vs-spaced 47% narrower → HarfBuzz joining PROVEN (f05b) |
| R06 | f06_invisible | INVISIBLE draws nothing | PASS (S67 A4+F-124) | all-white frame = correct; was black |
| R08 | f08_canvasops | per-op canvas census | PASS 10/10 | per-op pixel table |
| R09 | f08_canvasops (R6) | clipRect | NO-OP pixel-proven | 245 leak px (B2 registered) |
| R09b | f08_canvasops (R5/R7) | scale/rotate | NO-OP pixel-proven | gray at unscaled coords (B1 registered) |
| L11 | f11_linear | LL weights 1:1:1 | PASS 10/10 | 640px thirds + VT geometry |
| L13 | f13_frame | FrameLayout gravity | PASS 7/7 | TL/center/BR exact |
| L14 | f14_relative | RL rules | PASS 8/8 | 4 rules pixel-exact |
| L18 | f18_lltop | LL cross-axis TOP | PASS (S67 C3 fix) | child y=0 (was y=760) |
| I21 | f21_button | button click → state → text | PASS | click report 1584px, STATE=1 |
| LC27 | f27_nav | startActivity click→B render | PASS (S67 F-121 fix) | 2073273px, B bg #CCEEFF |
| RES31/32 | f31_resources | @string/@color + API path | PASS | brand bg + VT text |
| RES37 | f32_dimen | dimen density law | PASS (S67 A2 fix) | PX=263 (AOSP exact) |
| RT38 | f38_identity | object identity | PASS | IDENT=true,false,v=42 |
| RT39-45 | f39_44_runtime | null/arrays/reflection/super/interface/static/field/wide | PASS | 11-token VT text all correct |
| LC28/29 | f26_lifecycle | ctor + field-init order | PASS | INIT=6,5 |
| RT45 | f45_exceptions | AIOOBE catch/finally | PASS | EXC=CAUGHT_AIOOBE |

## Real APK cross-validation (user §18)

| APK | Recipe | Result |
|---|---|---|
| TicTacToe golden | --click-count 9 | initial 613cfccc… + win 2e80e8c0… BYTE-MATCH S66 records |
| FishRings S10 | s65_revalidate tap chain | 5/5 frames BYTE-MATCH S66 (splash→board→blue→pink) |
| OPMT S6 | s65 tap recipe | menu 62619caa… + game 9801d008… BYTE-MATCH S66 |
| TriPeaks S7 | s65 probe | splash 31ddd4d5… + lobby b513d78b… BYTE-MATCH S66; board (R-NEW-388) unchanged PARTIAL |
| HelloWorld / gmdice | queued | need re-build from fixtures (WAVE 9); fixtures exist |
| miniandroid_test | make test | 4/4 PASS |
