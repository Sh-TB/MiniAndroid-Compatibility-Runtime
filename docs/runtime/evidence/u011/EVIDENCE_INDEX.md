# UNIFIED_011 Evidence Index — recovered UNIFIED_007 resource pipeline

All images are **RUNTIME-RENDERED** by `build/miniandroid` during the UNIFIED_011
recovery session (2026-08-30, UTC+3), unless marked otherwise. They are render
proofs, not copied APK assets. Each file lists full provenance per CAMPAIGN 011 §24/§25.

Runtime commit at capture: UNIFIED_007-recovery (staged on top of `8f0a85b`).
Binary: clean rebuild (`make`), g++ 14.2, C++17.

---

## u011_telegram_v12_baseline_match.png

| field | value |
|---|---|
| origin | runtime-rendered screenshot (Telegram v12.10.1 full journey incl. click chain) |
| APK | Telegram 12.10.1 vc70389, SHA256 `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` |
| SHA256 (this file) | see SHA256SUMS_U011.txt |
| dimensions | 1080x1920 |
| non-white px | 41,233 |
| determinism | 3/3 runs identical SHA `06fb40da16b1f473980cfea9b0dc83d9d1707c2573cf713d636fd91d196503b3` |
| baseline | EXACT match to UNIFIED_002 recorded baseline (zero regression) |

## u011_gmdice_real_ui.png

| field | value |
|---|---|
| origin | runtime-rendered screenshot via UNIFIED_007 real inflation (ARSC -> AXML -> ViewShadow) |
| APK | GMDice de.duenndns.gmdice v8 (F-Droid), SHA256 `1621eda11b5dbc0c232b54c652d27aeab2f8a3c95be2c1f0632d6233b12d8a85` |
| inflate stats | root_id=4 views=10 strings=2 |
| semantics | REAL app UI: "Push buttons to roll!", "Long-press buttons to configure dice!", "Roll it!" button |
| HEAD baseline | `c200c521…` generic default screen (23,472 px) — REPLACED by real UI (158,040 px) |
| known limitation | glyph overlap/spacing artifacts (SFS-010 measure issue); UTF-8 overlap visible |

## u011_simplestopwatch_real_ui.png

| field | value |
|---|---|
| origin | runtime-rendered screenshot via UNIFIED_007 real inflation |
| APK | Simple Stopwatch omegacentauri.mobi.simplestopwatch v26 (F-Droid) |
| inflate stats | root_id=5 views=11 unresolved=2 |
| semantics | REAL controls: Start / Reset buttons, digit `0`, bottom button row |
| HEAD baseline | `c200c521…` generic default screen — REPLACED by real UI (930,980 px) |
| known limitation | layout weight/measure geometry wrong (buttons full-height) — documented as open measure bug |

---

## Negative results (honest record)

- **headingcalc**: inflates `views=3 strings=0` (`@string/` refs unresolved) -> would render
  blank; **UNIFIED_011 guard rejects non-substantive trees** -> falls back to legacy default
  screen `c200c521…` (byte-identical to HEAD baseline). Not committed as image (blank).
- **unote**: resource-obfuscated APK (`res/0s.xml` style paths) — ARSC name->path mapping fails,
  inflation aborts, fallback = baseline. Limitation recorded.
- **tictactoe / dooz**: blank white `c035e9ba…` on BOTH HEAD baseline and UNIFIED_011 build
  (byte-identical) — pre-existing, not a regression. dooz = known Compose blocker.
- **stopwatch**: exit 1 pre-existing (truncated APK; UNIFIED_002 androguard concurs).
- **telegram_v12**: `U007-INFLATE` never fires (setContentView(int) not reached in journey);
  behavior unchanged, SHA identical — proves the new path is inert where not exercised.

Full per-run logs and matrix JSON: produced by `scripts/u011_test_matrix.py`
(kept out of Git per §26; summary embedded in MASTER_PROJECT_STATE_011.md).
