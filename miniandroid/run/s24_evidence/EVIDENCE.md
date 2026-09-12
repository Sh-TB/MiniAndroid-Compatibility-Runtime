# S24 — Runtime Compatibility Campaign evidence bundle

Session law: no `rc=0` theater — every claim carries its command, its raw
artifacts, and its honest status marker (VERIFIED-FIXED / OBSERVED / PARTIAL /
BLOCKED).

## Target: Dooz (io.github.yamin8000.dooz_18.apk, F-Droid Tic-Tac-Toe, Jetpack Compose)

Standard command (attach gate is the documented UC009-WIRE env for
Compose-based apps; zero other overrides):

```
cd miniandroid
MINIANDROID_DISPATCH_ATTACH=1 ./build/miniandroid run \
    -o run/s24_post_f090i download/exp076_corpus/io.github.yamin8000.dooz_18.apk
```

- Final state: **rc=1 (honest)** — composition, AndroidX Navigation setup,
  NavHost graph build, and start-destination navigation all execute; the run
  dies at R-NEW-323 (root-graph back-stack entry law).
- `report.md`, `screenshot.png` — final frame (placeholder pending first
  composed UI; 802/2,073,600 non-white px, deterministic).
- `final_stderr.txt` — full engine trace of the final run (uncaught-exception
  chain, lifecycle dispatch, compose node trace).
- `dooz_det{1,2,3}.png` — three independent runs, byte-identical
  (sha256 193466ead8fd21d6… ×3) — determinism holds at the frontier.

## Barrier chain closed this session (all VERIFIED-FIXED, engine-generic)

| # | Root | Fix | Proof |
|---|------|-----|-------|
| 1 | R-NEW-316 check-cast identity law | F-090 | [S24-GETCLASS-OBJ] probe: heap desc `Landroidx/navigation/compose/e;` vs register `Ljava/lang/Object;` |
| 2 | R-NEW-317 ViewShadow routing dead code | F-090c | [S24-BRIDGE]+[TAG-TRACE]: getTag(8) never reached ViewShadow before fix; parent walk 102→8→101 works after |
| 3 | R-NEW-318 interface bridge runtime-class law (+String.charAt, Character.isWhitespace/SpaceChar) | F-090d/e/f | route IAE gone; `game`/`settings`/`about` accepted by NavDestination.setRoute |
| 4 | R-NEW-319 java.util.UUID absent | F-090g | UUID NPE gone; deterministic v4-form UUIDs |
| 5 | R-NEW-320 collection copy-constructor law | F-090h | [S24-COLL]: copy map 2752 empty before fix; Navigator attach loop executes state iput after |
| 6 | R-NEW-322 exact-descriptor overload law | F-090i | [S24-ADDALL]/[S24-TRI]: caller arg obj#2831 non-null; wrong-overload body executed before fix |

## Current frontier (open, next session)

R-NEW-323 — `IAE "No destination with ID 0 is on the NavController's back
stack. The current destination is e$a@2554"`. The root GRAPH's own
NavBackStackEntry (routeless graph ⇒ id 0) is never pushed; upstream pushes
ancestor-graph entries during navigate before destination entries (DEX:
`c.o` builds per-graph-hop entry levels and dispatches `Navigator.navigate`
per level; `c$e.o`/`d.o` mirror entries into the NavController back stack via
`c.a` with the ancestor slice).

## Regression proof (all at this session's HEAD)

- Full battery: `bash scripts/test/run_test_battery.sh --skip-build` →
  92 stages, **91 PASS**, 1 FAIL = pre-existing GATE H (simplestopwatch glyph
  crop — unchanged, honestly registered).
- Hello Color golden: APK rebuilt from fixture byte-identical
  (77863f1f5e865f56…), 3 runs rc=0, screenshot sha256 11e0056320d8546d… ×3 ==
  committed golden frame.
- ChessClock: rc=0, screenshot sha256 e4a2d7c90cd2fd26… == S22/MC3 record,
  2,073,600/2,073,600 non-white.
- Dooz: 3× byte-identical (rc=1 honestly marked, frontier R-NEW-323).
