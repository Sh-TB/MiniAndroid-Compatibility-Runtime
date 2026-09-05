# CAMPAIGN FINAL REPORT — Deep Compatibility Campaign (Task 8 + 9)

> SUPERSEDED-AS-LATEST: the newest campaign report is
> `docs/CAMPAIGN_FINAL_REPORT_REUSE_FIRST_PROGRESS.md` (2026-09-05).
> This file is preserved as the historical record of its own campaign.

Base: sandbox-reset snapshot `0edb52b` → campaign commits `de5f370`,
`c7bb9f2`, reference-matrix commit, audit commit.
Date: 2026-09-05. All evidence runtime-produced on current HEAD; zero-skip
counting enforced in every validator.

## §23 Required evidence table

| Subsystem | Status | Evidence |
|---|---|---|
| APK loading | PASS | 13/15 corpus APKs hash-verified + launched (fetch_corpus.py); fixture toolchain ECJ→D8→ZIP |
| DEX execution | PASS | semantic battery 118/118 (14+55+25+5+8+6+5); tictactoe_golden 9/9 real-DEX clicks |
| Activity lifecycle | PASS | tictactoe_golden onCreate→setContentView→measure→render→click chains |
| Resource/ARSC | PASS | ARSC-first values (chessclock strings=38 colors=8); baselines green |
| res/font | FAIL (open) | no corpus APK carries res/font; needs synthetic-ARSC fixture (documented) |
| assets/fonts | PASS | tictactoe 1/1 registered; openlauncher 6/6 registered (root-assets path — generic, not hardcoded) |
| system/default font | PASS | NO_FONT_DIRECTORY apps emit source=SYSTEM (simplestopwatch, dice) |
| Typeface | PARTIAL | createFromAsset + setTypeface proven; Typeface.create/family+style Fixture D/E pending |
| Text shaping | PASS | FriBidi/HarfBuzz/FreeType real pipeline; char_probe 8/8 primitive semantics |
| Measure | PASS | weighted LinearLayout rows/cells pixel-verified in tictactoe_golden |
| Layout | PASS | 9-button board fills frame; status WRAP_CONTENT; baselines unchanged |
| Canvas | PASS | Cycle E validator ALL PASS (cubic/rMoveTo/rLineTo/offset/oval/arc/winding/even-odd/stroke) |
| Path | PASS | same — frame SHA 64c8398e… reproduced across sandbox resets |
| Renderer | PASS | walk renders programmatic trees; fonts::layout_text drives paint |
| Framebuffer | PASS | nonwhite accounting + per-frame SHA manifest in every run |
| Input | PASS | tictactoe_golden 9/9 dispatches; frozen-game early returns correct |
| State transition | PASS | turn alternation, win detection, gameOver freeze — text + pixel evidence |
| Deterministic replay | PASS | 10-frame run A/B byte-identical; frames 7/8/9 identical |
| Tic-Tac-Toe (golden) | PASS | **validate_tictactoe_golden.sh ALL PASS** — the §10 milestone |
| HelloWorld golden | PASS | docs/demo proof (click→state→frames, VALIDATION_PASS, Task-7) |
| Telegram | BLOCKED | official download serves 1.2 MB stub vs pinned 82 MB hash; fetch rejects |
| WineDroid study | COMPLETE (site level) | identity RESOLVED: winedroid.soham.sh — Rust Android userspace compat layer; GPL-3.0; repo private → SITE_DOCS_READ evidence, 13 pages read |
| Reference matrix | COMPLETE | 15×10 rows; licenses re-verified at HEAD; evidence legend |
| Agent finding audit | COMPLETE | docs/AGENT_FINDING_AUDIT.md — 118/118 battery, RESULT_012/013 claims obsolete (implemented), all rows evidence-linked |
| Git commit | PASS | de5f370 + c7bb9f2 + reference + audit commits |
| Git push | BLOCKED | sandbox has no remote ("fatal: No configured push destination") — commits clean, fast-forward-ready |
| Remote verification | BLOCKED | follows push |
| README evidence | PASS | real runtime screenshot pair with SHA-256 provenance |

## Key deliverables this campaign

1. **ONE COMPLETE APK (§10)** — `tictactoe_golden`: real APK, real DEX
   listeners, weighted programmatic UI, click→state→pixel→replay chain.
2. **Six generic engine fixes** uncovered by the fixture (LayoutParams
   constructors bridge, setContentView(View) measure pass, signature-aware
   return/param typing for Z/C/B/S, integer-like compare law, synthetic
   accessor throttle exemption, String.valueOf) — each
   probe-discriminated before/after by `char_probe` (8/8).
3. **Reference study** — WineDroid identity resolved after multiple
   BLOCKED sessions; matrix upgraded with honest evidence levels.
4. **Agent-finding audit** — every RESULT_* classified with an
   independent current-HEAD probe; two stale agent claims corrected.

## Remaining blockers (honest)

- res/font ARSC-managed chain (needs synthetic-ARSC fixture tooling)
- Typeface.create / family+style fixtures D/E
- libGDX/GL boundary (tictactoe-emmanuelmess blank), Compose/AndroidX
  depth (dooz partial), stopwatch-muellerma AppCompat PARTIAL — all
  documented with reproducible SHAs
- Telegram artifact acquisition + GitHub push credentials
