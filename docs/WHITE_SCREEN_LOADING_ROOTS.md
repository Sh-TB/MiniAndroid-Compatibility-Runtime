# WHITE SCREEN LOADING ROOTS — classification with first-missing-stage evidence

> LOADING-CAMPAIGN (2026-10-03). The law (§21 of the master request): do NOT
> label "white screen = file bug" unless the trace proves it. Each case below
> carries its FIRST_MISSING stage from the F-NEW-233 unconditional frame-truth
> census and the loading-audit live probes.

## Classification law

```text
BOOT → Activity → ViewTree → resource loading → file loading → asset loading
     → state → render → screenshot
```
`FIRST_MISSING` = the earliest stage whose expected observable did not occur.
Loading roots (RESOURCE_RESOLUTION / ASSET_OPEN / FILE_OPEN / STREAM / FD /
DECODE) are attributable to this campaign's fixes. Non-loading roots
(WINDOW_ROOT / APP_DRAW_OPS / LOOPER / ACTIVITY_NAVIGATION / COMPOSE /
CONSUMER) are NOT file bugs and must not be claimed as loading wins.

## Case table

| Case | Face | FIRST_MISSING | Loading-caused? | Evidence |
|---|---|---|---|---|
| sudoku (plain run) | white | `WINDOW_ROOT` (verdict=NO_ROOT) | **NO** — window/content-root chain, not a byte source | F-NEW-233 verdict record (MEGA-W2) |
| whatsapp | white | window/content chain (golden REJECTED) | **NO** — same class as sudoku | F-NEW-230/233 records |
| telegram settings-face | renders (2-face) | `ACTIVITY_NAVIGATION` (intro/auth chain) | **NO** — loading works (7 asset OPENs provenanced, prefs ×21); the missing piece is navigation | tg_r1 trace + frame bbb6cd10a834963d |
| opencalc pre-F-NEW-220 empty-shell | empty frame | `VIEW_BIND`/content-parent | **NO** — F-NEW-220 content-parent reuse closed it | F-NEW-220 record |
| dooz pre-R-NEW-347 | blank compose | compose composition chain | **NO** — R-NEW-347/345 family | root registry |
| probe-observed empty-file faces | blank image/file UI | `STREAM`/`DECODE` | **YES — closed this campaign**: read(byte[]) fill, BAOS, decodeStream, decodeFile path law | probe gate asserts (r1..r10 logs) |
| probe-observed silent-empty config faces | wrong/empty UI state | `ASSET_OPEN` (fake-success) | **YES — closed**: R-1 FileNotFoundException contract + R-7 list | probe asset-missing=FNFE-HONEST |
| probe-observed persistence loss | state resets | `FILE_OPEN` (write void) | **YES — closed**: ST-2 write family + atomic prefs + restart counter | probe prefs-runs 1→2→3 |

## Bottom line

- The corpus's visible white/blank faces (sudoku, whatsapp) are **NOT
  loading-caused** — their first-missing stages sit above the byte layer
  (window/content/compose/navigation). No loading fix can be honestly
  claimed for them.
- The loading-caused blank/wrong-content class was proven with the synthetic
  probe (the real corpus never exercised those APIs — see
  `docs/WORKING_APP_LOADING_EXPLANATIONS.md`) and **closed generically**:
  stream/FD family, asset contract, write family, path law, decodeStream.
- The runtime can now answer "was THIS app's blank frame a loading failure?"
  from the trace: `MINIANDROID_FILE_IO=<out>` + F-NEW-233 verdict give the
  first-missing stage per frame (K answer: YES).
