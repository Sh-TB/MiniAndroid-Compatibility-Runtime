# CONT-29 / TRACK B — SIMPLE CALCULATOR RETAINED: FULL SUCCESS ×3, ZERO DRIFT

Wave: CONT-29. Track B's success condition was delivered in CONT-27 (first
FULL SUCCESS) and re-proven in CONT-28. This wave re-proves retention at the
CONT-28 final binary with NO engine changes (the binary is byte-exact
`d35a60d43f83331c`, rebuilt from HEAD `baa6654c` — see
COMPOSE_RECOMPOSITION_ROOT.md §0), so this document records the retention
proof and the APK identity re-verification.

## 1. APK IDENTITY

| item | value |
|---|---|
| Simple Calculator vc8 | sha16 `68da25fd9fdf54b4` == the CONT-26/27/28 record EXACTLY |
| source | F-Droid archive re-download (CONT-28), local `tmp/cont26_apks/simplecalc_8.apk` |
| positive control | `fixtures/fnew253_probe` green (CONT-26/27/28 lineage, unchanged this wave) |

## 2. RETENTION RUNS (×3, byte-identical)

| run | rc | screenshot sha16 | verdict |
|---|---|---|---|
| simplecalc_r1 | 0 | `7960bce447ac6d8f` | SUCCESS |
| simplecalc_r2 | 0 | `7960bce447ac6d8f` | SUCCESS |
| simplecalc_r3 | 0 | `7960bce447ac6d8f` | SUCCESS |

rc-truth captured per call (CONT-22 law). The 3-run proof is the wave's
retention gate: the app's OWN keypad (display TextView '0', Buttons
mod/^/√/C, 7-8-9-÷, 4-5-6-*, 1-2-3, at the 270x262 grid, 121 unique colors)
renders deterministically at FULL SUCCESS.

## 3. HONEST SCOPE NOTE

The retained success is the RENDER proof delivered by CONT-27 (F-NEW-283
DEX-existence constructor authority). The NEXT Track B frontier remains
input-pump interactions (button taps driving real CalculatorState changes)
— registered in the CONT-27/28 evidence as the next wave target, unchanged
this wave (the wave's budget went to the Track A recomposition root).

## 4. STATUS

| item | status |
|---|---|
| Simple Calculator FULL SUCCESS retained ×3 at the wave binary | TESTED |
| Target APK byte-identity re-verified | TESTED |
| Input-pump interaction frontier | PENDING (next wave) |
