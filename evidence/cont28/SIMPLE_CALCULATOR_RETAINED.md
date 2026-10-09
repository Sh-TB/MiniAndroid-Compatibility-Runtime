# CONT-28 / TRACK B — SIMPLE CALCULATOR RETAINED (FULL SUCCESS STATE)

Wave: CONT-28. Track B's CONT-27 terminal state (Simple Calculator FIRST
FULL SUCCESS, F-NEW-283 DEX-existence inflate gate) is a committed claim and
was re-proven this wave at the new binary (two additional generic laws
landed: F-NEW-284 super-dispatch proto, F-NEW-285 RenderNode claim gate).

**VERDICT UP FRONT:** Simple Calculator retains its FULL SUCCESS state —
rc=0 ×3, the app's own keypad rendered, positive control re-run green. The
wave's Track A laws are regression-neutral for Track B (both live in the
invoke-super arm and the RenderNode claim — paths Simple Calculator's
view-based layouts never reach).

## 0. TRUTH LOCK

| item | value |
|---|---|
| binary (post-CONT-28) | `miniandroid/build/miniandroid` = `9c42dd61` + F-NEW-284 + F-NEW-285 + diagnostics |
| Simple Calculator APK | F-Droid archive vc8, re-downloaded THIS wave, sha16 `68da25fd9fdf54b4` == CONT-26/27 record EXACTLY (byte-identity of the target re-locked; archive reachable) |
| positive control | `fixtures/fnew253_probe` (built via `scripts/cont21_build_probes.sh`) |

## 1. DUAL CONTROL AT THE CONT-28 BINARY

- Simple Calculator ×3: rc=0 (FULL SUCCESS per the main.cpp rc-truth law),
  screenshot sha16 `7960bce447ac6d8f` byte-identical ×3 — the SAME sha
  CONT-26/27 recorded, now with the honest pixel reading (the app's own
  keypad; 121 colors — 6fa8dc blue keypad / fafafa bg / f68630 orange).
- fnew253_probe positive control: 147 PASS / 0 FAIL rows retained.

## 2. NO ROOT REGRESSION, NO DIVERGENCE MOVE

Track B's 12-stage chain (APK load → Application → ContentProvider →
androidx.startup → Activity → AppCompat → theme → setContentView →
view-tree → measure/layout → dispatchDraw → capture) runs clean at the
CONT-28 binary — identical to the CONT-27 record. The two new laws touch:

1. `execute_invoke_super` proto passing — Simple Calculator's super-calls
   (AppCompat delegate.onCreate etc.) were ALREADY resolved by the F-280
   exact-descriptor law at their call sites; carrying the proto narrows
   overload selection for every caller, and the ×3 byte-identical anchors
   prove neutrality where the law's answer was previously correct-by-shape.
2. `handles_class` RenderNode family claim — Simple Calculator draws through
   the classic View/Canvas pipeline; no RenderNode call exists in its DEX.

## 3. STATUS LEDGER

| item | status |
|---|---|
| Simple Calculator FULL SUCCESS retained (rc=0 ×3, byte-identical) | TESTED |
| Positive control fnew253_probe 147/0 | TESTED |
| Theme/startup hypothesis bookkeeping | unchanged (materialAlertDialogTheme/colorSurface rejected in CONT-26 by execution order) |
| Next Track B frontier | button interaction (input-pump family) beyond the 5-frame sweep — unchanged from CONT-27 |
