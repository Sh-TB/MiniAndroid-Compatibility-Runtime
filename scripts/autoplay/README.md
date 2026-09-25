# MiniAndroid Autoplay — ONE place for every autonomous-play driver

> S100 (owner mandate): all auto-plays live HERE, with one documented
> standard structure, so any app or game can be driven by a standard
> autoplay. Nothing autoplay-related lives scattered in `scripts/` anymore.

## Layout

```
scripts/autoplay/
  common.py                 # the STANDARD structure (launch→interact→measure→evidence)
  run_all.py                # batch runner over the roster (optimization: one command)
  s80_2048_autoplay.py      # 2048 swipe-schedule driver
  s80_sd_autoplay.py        # Snake Deluxe BFS driver (wrap-aware since snake-neon)
  s80_tet_autoplay.py       # Mini Tetris tick-anchor driver
  s83_ttt_autoplay.py       # TicTacToe 9-leg driver
  s98_minicraft_autoplay.py # Minicraft house-building driver (cottage 113,190 px)
  s98_snakeneon_autoplay.py # Snake Neon wrap-BFS + reverse-guard + tick law
  s99_full_load.py          # corpus full-load wave runner (obs+click protocol)
  s98_games_full_load.py    # S98 roster runner
```

## The standard autoplay structure (`common.py`)

| Stage | API | Law |
|-------|-----|-----|
| 1 LAUNCH | `run_mini(rundir, apk, frames, taps)` | real-dalvik, fixed frame budget, deterministic virtual clock |
| 2 INTERACT | `--tap x,y@frame` schedule | REAL dispatches through TouchDispatcher (G06 token evidence); no synthetic state writes |
| 3 MEASURE | `state_change_px(frame_a, frame_b)` | exact differing-pixel count; "tap dispatched" is NEVER the final proof (state-change law) |
| 4 EVIDENCE | `write_record(...)` | `run/autoplay/<title>/autoplay_record.json`: APK SHA, screenshot SHA, px deltas, taps |

**Full protocol**: `common.standard_run(title, apk, frames, taps)` runs all
four stages and writes the record.

## Laws every driver must respect

1. **3-run repeatability** — run the driver 3x; byte-identical screenshots
   preferred; variance recorded honestly (S100 §25).
2. **1-move = 2-frames tick law** — timing-scheduled games advance one tick
   per two captured frames (snake-neon law); never sleep-hack the host
   (no global sleeps/delays — S100 §27 performance safety).
3. **Zero-APK law** — APK files are re-fetched from their SHA-pinned
   manifests; never committed.
4. **Honesty** — a run that reaches menu-only states is recorded PARTIAL,
   never VERIFIED; failures become issue-per-problem tickets.
5. **Tick-anchor drift finding** (Tetris, GAMES-6 #339) stays OPEN until a
   semantic fix, not silenced by an autoplay hack.

## Batch runner (optimization)

```bash
# run the whole roster (or a subset) with consistent output + records:
python3 scripts/autoplay/run_all.py                 # everything registered
python3 scripts/autoplay/run_all.py snake-deluxe 2048
```

`run_all.py` reuses ONE runtime process per title run (no redundant loads),
writes every record under `run/autoplay/<title>/`, and prints a summary
table (rc, state-change px, determinism vs the previous run).
