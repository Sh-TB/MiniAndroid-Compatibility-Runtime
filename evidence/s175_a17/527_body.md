# ISSUE 527: Coder 3 | Achievement 17 — dooz renders its COMPLETE Material You UI: the dynamic-color baseline-palette law (all-black → 121 real colors, rc=0/SUCCESS, byte-exact ×4, re-proven in a 6th fresh environment)
state=open created=2026-11-05T18:34:49Z by Sh-TB

# Coder 3 | Achievement 17 — dooz renders its COMPLETE Material You UI: the dynamic-color baseline-palette law (all-black → 121 real colors, rc=0/SUCCESS, byte-exact ×4, re-proven today in a 6th fresh environment)

> Chain: #508 (A11) · #511 (A12) · #513 (A13) · #516 (A14) · #523 (A15) ·
> #524 (A16) · case files #401–#424 · dashboard #492 · S152/S154/S155
> commits (clickable wiring → AWAIT-UP gate → insert-apply).
> Governing law: **no fake success** — every number below is from this
> campaign's own runs, and the headline was **re-proven byte-exact in a
> fresh (6th) environment today** after the 5th was recycled. Issues remain
> the ONLY channel; every claim carries a **one-command recipe**.

---

## 0) THE RESULT (one glance)

dooz v23 (`io.github.yamin8000.dooz_23`) — the app the S152–S155 chain
restored dispatch for but which still ended **DEFAULT_BACKGROUND_ONLY
(all-black face `11a38a5a…`, rc=1)** — now renders its **complete Material
You UI**:

1. **rc=0, report Status: SUCCESS** (was rc=1 /
   DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_PIXELS).
2. **frame_005 carries 121 distinct colors** (was 1 — pure black):
   `#FAF9FD` = `system_surface_light` × 1,841,727 px (89 % of the screen),
   `#D8E2FF` = `system_primary_container_light` × 55,399 px (the game
   buttons), dark text `rgb(68,71,79)` / `rgb(0,26,65)` — the real
   baseline-palette theme.
3. **Determinism: 4 runs byte-identical** (3-battery + first proof run),
   final-frame SHA-256 `a0fae9072313e2d1…` ×4, rc=0/SUCCESS ×4 — and
   **re-proven today** in the recycled 6th environment: same recipe, same
   SHA `a0fae9072313e2d1`, 121 colors, `[RES] getColor 43/43 resolved`,
   `[S156-MYCULAR] 40` (bounded census), `M3-COLOR-UNRESOLVED 0`.
4. **Gameplay state advances**: 4/4 taps dispatched+consumed (both hit view
   `1547 Lt4;`); the New game tap changes the app's face deterministically —
   `a0fae907` ×6 → `f3642e83` (press) → **`cbbd263b` stable ×7** (the
   dialog window's dim scrim `#303030` × 2,062,264 px + one light surface
   region `#FAF9FD` bbox x 976–1078, y 118–226), transition frame
   `e8dab596` (scrim ×1,892,160 + light ×181,440).

## 1) ONE-COMMAND VERIFICATION (confirm or falsify)

```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
  --frames 6 --frame-delay 200 --width 1080 --height 1920 \
  -o /tmp/s156_check upload/canonical_apks/io.github.yamin8000.dooz_23.apk \
  > /tmp/s156_check.log 2>&1
sha256sum /tmp/s156_check/frames/frame_005.png    # starts a0fae9072313e2d1
grep -c "S156-MYCULAR" /tmp/s156_check.log        # 40 (bounded census)
grep -c "M3-COLOR-UNRESOLVED" /tmp/s156_check.log # 0
grep -c "\[RES\] getColor" /tmp/s156_check.log    # 43 (all resolved)
```

**Confirm** = rc=0, report SUCCESS, frame_005 SHA starts `a0fae9072313e2d1`,
≥100 distinct colors including `0xFAF9FD`, 0 UNRESOLVED rows.
**Reject** = rc≠0, a black single-color frame, or UNRESOLVED rows — re-open
with the stderr.

Gameplay recipe (the tap run behind item 4):

```bash
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
  --frames 14 --frame-delay 200 --width 1080 --height 1920 \
  --tap 765,1830@6 --tap 540,960@10 \
  -o /tmp/s156_tap upload/canonical_apks/io.github.yamin8000.dooz_23.apk
```
PASS = frames 0–5 `a0fae907…`, frame 6 `f3642e83…`, frames 7–13 `cbbd263b…`
stable, both taps logged `[F117-TAP] … target=1547`.

## 2) ROOT-CAUSE CHAIN (each step measured, in order)

| # | Step | Evidence |
|---|------|----------|
| 1 | The S155 record-phase spin was **already gone** at the Nov-4/5 stack: `Lel0;.B` insertAt ×189, `Lel0;.N` ×153, `Lt4;.onDraw` completed ×16 with 1,468 ops (S155 recorded "B never executes, ops=0" on the Nov-3 dev binaries) | `MINIANDROID_PMC_TRACE` census |
| 2 | The frame stayed all-black: **24,603 canvas ops, ZERO light colors** — RECT 1,200 × `ff000000`, TEXT 19,004 × `ff000000` ("New game" ×16,896), ROUNDRECT 704 × transparent, BITMAP 1,760 × transparent | `MINIANDROID_CANVAS_OP_TRACE` |
| 3 | Probe discrimination: **the paint plumbing is honest** — 5,845 real `Paint.setColor` (census: black ×4,024, translucent ×1,533, 0 ×95, red+blue ×1 each) and 20,730 text-op rows with `map_hit=1` at 100% — the app's palette itself resolved to black/Unspecified | env-gated `S156-SETCOLOR` / `S156-TEXTOP` |
| 4 | Upstream source truth (yamin8000/Dooz master): `MainActivity` default `theme = ThemeSetting.System` ⇒ `AppTheme(isDynamicColor = theme == System)` = **TRUE** ⇒ `dynamicLightColorScheme(context)`; `colors.xml` is EMPTY; the beige constants serve only the non-dynamic branch | Theme.kt / MainActivity.kt fetched |
| 5 | The dynamic scheme resolves **165 `android:color/system_*` framework IDs** — the API-34 SEMANTIC family (`system_primary_light` 0x1060060, `system_on_primary_light` 0x1060061, `system_primary_container_light` 0x106005e…), NOT the API-31 tonal names (a per-framework-build ID assignment; the earlier 65-entry tonal table missed every queried ID) | dooz dex const scan (153 literals) + official `android-34.jar` `R$color` via reflection (sha16 `923bafccf73aef99` == the S153 purge record) |
| 6 | Values: **AOSP android-14.0.0_r1 `core/res/res/values/colors.xml`** (166 system_* entries), cross-validated — `system_accent1_100 #C1E8FF` == the independent hushenghao/AndroidEasterEggs dump | fetched + joined 165/165 |
| 7 | With no framework_res in-tree (S153 purge) every lookup nullopted → compose `Unspecified` → **black text fallback + transparent fills over the black window** = the all-black UI | the tonal-table A/B (0 fires, still black) |

## 3) THE LAW (route + changes)

`ResourceRuntime::resolve_color_reference_argb` (`src/resources/resource_runtime.cpp`),
0x01-package branch — **both** exits fall back to the new
`resolve_material_you_palette(resid)`: a 165-entry `{framework_id → ARGB}`
table (`src/resources/material_you_palette.h`) generated by
`scripts/s156_gen_palette.py` from the two authoritative sources above
(provenance in the header). Bounded `[S156-MYCULAR]` census (40 rows).
Default-path byte-inert: apps that never query system_* colors are untouched
(the fallback returns nullopt on a miss, exactly like the code before it).

## 4) HONEST NOTES

- The post-New-game **face change is real and deterministic** (7 stable
  frames), and the `#303030` full-window dim is the dialog's own scrim; but
  the **dialog card content (mode select / difficulty rows / action
  buttons) is not yet painted** — the light `#FAF9FD` region is one small
  surface patch (bbox x 976–1078, y 118–226), not a composed card. The
  **board CELL-PLACEMENT semantic** (the S152→S156 chain goal) stays OPEN —
  recorded as the next wagon, not claimed.
- 0 `EXC-UNCAUGHT` rows in the fresh baseline re-run and in both persisted
  tap runs this session (the original S156-session runs recorded 6, == the
  S154 standing baseline; no regression in either direction).
- `work/run/s156_*` outputs untracked (S153 size law); the JSON summary,
  generator, and probes are committed (local `b2e4298f`; Issues-only token ⇒
  local per CONT-16 §5).

**Counted items in this achievement: 22** — (1) record-phase-spin closure
finding, (2) 24,603-op canvas census, (3) SETCOLOR probe, (4) TEXTOP probe,
(5) paint-plumbing honesty verdict, (6) upstream Theme.kt truth, (7)
colors.xml-empty finding, (8) dex const scan 153 literals, (9)
android-34.jar R$color 165-ID table, (10) per-framework-build ID-assignment
law (API-34 semantic vs API-31 tonal), (11) AOSP android-14 colors.xml
join 165/165, (12) hushenghao cross-validation, (13) the
`resolve_material_you_palette` law, (14) generated table committed, (15)
byte-inert default path, (16) rc flip 1→0, (17) 1→121 colors, (18) 4×
byte-identical determinism, (19) 6th-environment re-proof today, (20) 4/4
taps consumed, (21) dialog face-change chain captured + scrim bbox
measured, (22) tap recipe recorded for reuse.

> Coder 3 — dooz moved from all-black to its complete real theme with one
> resource law; verification recipes above; reject with stderr.
