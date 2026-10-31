# S138 LIGHT TRAINS 11–30 — the 20 small fast wagons

> User directive (2026-11-01): «قطار ریزه میزه سریع، واگن‌های کم‌حجم … ۲۰ تا قطار بر اساس فرضیات
> و مشکلات احتمالی بساز، یکی یکی بررسی بکن … ۱۰ برنامه رو همیشه بذار تو لیست».
> Head: **85600efd** (origin/main, TRAIN-10 — local was behind; reset --hard per the standing
> GitHub-is-newer directive). Each train = ONE assumption, ONE quick check, ONE verdict.
> Evidence: [evidence/s138_trains/light_trains_11_30.json](../evidence/s138_trains/light_trains_11_30.json)
> · Standing queue: [docs/PROGRAM_QUEUE.json](PROGRAM_QUEUE.json) · Snapshot: train30_capability_snapshot.json

## Station A — dooz fix probes (the 4 TRAIN-10-banked probes, executed light)

| Train | Assumption | Check (banked 1.6.7 sources / registry) | Verdict |
|---|---|---|---|
| 11 | keyed composed() impl locatable without a rebuild | ComposedModifier.kt lines 78/110/143/173: KeyedComposedModifier1/2/3/N | VERIFIED — dex locator banked (R8-merged keyed classes) |
| 12 | drop site = TYPE test on R8-merged keyed class | F-NEW-259 family ROOT-CAUSED-FIXED (descriptor-slot law) | PRIME SUSPECT confirmed; extend VALUE→TYPE tests |
| 13 | M3 Surface(onClick) = same clickable family | Clickable.kt 1.6.7 line 90: `clickable(...) = composed(`; line 21 import detectTapAndPress == the dooz FAB handler | **PROVEN GENERIC — the fix advances every M3 button app** |
| 14 | generic insertion point exists | try_recursive_invoke machinery + bounded 16-hop descriptor-slot fallback | BANKED — TRAIN-11-fix design, zero app knowledge |

## Station B — the standing 10-program queue (one wagon per program)

| # | Program | Now | Next wagon |
|---|---|---|---|
| 1 | dooz | anchor 851cc176; board absent; root pinned | TRAIN-11 fix train |
| 2 | opencalc | anchor 63020bc7 byte-exact ×3 | post-fix click probe |
| 3 | chess | anchor 3f7e6707 byte-exact ×3 | post-fix interaction probe |
| 4 | microtimer | anchor bbd350b6; VERIFIED L2 | timer start/stop probe |
| 5 | unote | anchor 7481e9b4; VERIFIED L2 | note-add + text input probe |
| 6 | tower3d | anchor 11a38a5a (3D-title anchor renders) | shares the generic draw-chain fix |
| 7 | 2048 | PLAYED (interaction+state-change) | L6+ promotion |
| 8 | tetris | interacted; VISUALLY_PARTIAL L3 | close the partial delta |
| 9 | snake-deluxe | PLAYED, GIF evidence | L6+ promotion |
| 10 | minicraft | PLAYED | L6+ + persistence probe |

Satellites: Telegram (260-frame run, +24 vs cont47; next = canned langpack response) ·
Freebloks 3D (first run, background only; APP_DRAW_OPS station) · EndlessTunnel (banked).

## Station C — assumption trains

- **25** «interaction = full game» → GAP MAPPED: input machinery proven on 13 titles; the gap is compose-app-specific, NOT game-wide.
- **26** draw frontier generic → CONFIRMED (Freebloks 3D = same family as dooz) — one canvas-bridge fix advances 2D AND 3D.
- **27** 3D answer → PARTIAL: tower3d anchor byte-exact + Freebloks first-run; gap = the same draw chain.
- **28** Telegram movement → MEASURED: 260/260 frames, themed partial face; remaining = langpack canned + 2 known boundaries.
- **29** regression integrity → ZERO DRIFT at 85600efd (anchors 6/6 ×3, negatives 19/19, skill 13/13).
- **30** capability snapshot → BANKED (150 titles · 853 roots · interacted 13 · state-change 12).

ZERO-LOG: shas + line numbers only; no logs/screenshots/APKs committed; engine UNCHANGED this series.
