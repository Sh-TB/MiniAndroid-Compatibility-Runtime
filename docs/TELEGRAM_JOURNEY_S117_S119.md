# TELEGRAM JOURNEY — S117 → S119 (reconstructed)

> RECONSTRUCTED DOCUMENT (continuation §5 M2). The original file was never committed; this reconstruction uses only preserved repo evidence (worklog, ledgers, scripts, evidence dirs). Every claim below carries its source. Where the original wording is unrecoverable, this reconstruction says so.

---

## 0. Why this file exists (the dead-preview-link record)

The original `TELEGRAM_JOURNEY_S117_S119.md` was announced in Telegram-issue comments
(#355/#356, 2026-09-29) as "published" via an external preview-host download link. That
host is dead and the markdown was never committed. Preserved record of the failure:

| Source | What it says |
|---|---|
| `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl` row `FR-NI-006` | "published as external preview download" — claimed_status `published`, verified_status **UNVERIFIED_CLAIM**, level **E0**: "The preview-host URL is DEAD and the markdown was never committed to the repository; content survives only inside issue comments. Committed copy required." |
| `docs/FORENSIC_UNVERIFIED_CLAIMS.md` §U1 | Same finding; missing evidence = "an in-repo copy of the document". |
| `docs/FORENSIC_MISSING_EVIDENCE.md` §M2 | "Missing: `docs/TELEGRAM_JOURNEY_S117_S119.md` … Source: #355/#356 comment text (preserved) + the session worklog." |
| `worklog.md` (forensic wave key findings) | "TELEGRAM_JOURNEY_S117_S119.md never committed (dead preview link) -> UNVERIFIED_CLAIM". |
| Git history (checked at reconstruction) | `git log --all -- docs/TELEGRAM_JOURNEY_S117_S119.md` → **zero commits**. |

This file is the committed copy demanded by FR-NI-006/M2 — a **reconstruction from
preserved repo evidence**, not a recovery of the lost text. The original wording (its
narrative, images, anything that lived only in the dead preview or unquoted issue
comments) is **unrecoverable** and is not invented here. Written by the continuation §5
M2 task (CONT-T5-M2); **not committed** by this task — left in the working tree for
normal review/commit flow.

---

## 1. The two Telegrams of this journey (official vs forkgram)

| | **forkgram classic** | **official Telegram** |
|---|---|---|
| Package | `org.forkgram.classic` | `org.telegram.messenger.web` (MC4 record) / `org.telegram.messenger` (registry APP-012) |
| Version | 12.10.8.0, vc 709208 | 12.10.1, vc 70389 |
| APK SHA pin (source-given) | `3baeecb3` (worklog S115; `evidence/s115_telegram/REPORT.md` line 1; F-Droid) | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` (full SHA-256, `docs/evidence/mc4_telegram/EVIDENCE.json` + `SHAS.txt`; official `https://telegram.org/dl/android/apk`, CDN-signed link fetched 2026-09-11, 73,028,244 bytes) |
| Repo-committed run evidence | `evidence/s108_telegram/`, `s109_telegram/`, `s110_telegram/`, `s115_telegram/`, `docs/evidence/mc4_telegram/` | `docs/evidence/mc4_telegram/` (v12.10.1, pre-window); **no S117→S119-window official-APK run artifact committed** (gap G1) |
| Role | Deep-execution chain APK (S107→S115: singleton death → full init → real login UI tree → first 0-error run); its login-pixel frontier is the named carry-in to S117 | User-facing goal APK (issues #16/#356); its S117→S119 campaign is recorded **only** in #356 comments, summarized by ledger row FR-356 |

MC4 honesty limits, verbatim: `"classification": "REAL APK FRONTIER — not claimed
usable"`; "no success is claimed beyond parse/launch/themed-window paint."

---

## 2. What the S117→S119 window actually contains (honest finding)

From `worklog.md` sections **S117/S118/S119** (the preserved ground truth for those
session IDs):

- **S117** — "MORE APPS/GAMES WITH COMPLETE GRAPHICS": PPM GitHub hygiene (`45a6b011`),
  rebuild, six generic HTML5/CSS/SVG laws, battery `scripts/s117_complete_graphics.py`.
  Telegram appears (a) in the S117 code commit description "fragment/createView disasm
  + scene work", preserved as `scripts/s117_disasm_createview.py` (forkgram APK,
  `Lorg/telegram/ui/nr1;.createView`), and (b) in the open-frontier list: "Telegram
  login pixels (R$styleable/text-draw)".
- **S118** — "COMPLETE-THE-INCOMPLETE", directive **"Telegram deprioritized for now"**:
  eleven generic laws (`09f5000f`). Zero Telegram-specific work.
- **S119** — native games (dooz flagship, driver recalibration, `34f462e6`); Telegram
  "(deprioritized per directive)".

Meanwhile ledger row **FR-356** ("[TELEGRAM] Official Telegram S117->S119 — complete
first-person journey changelog", #356, dated 2026-09-29) records an official-APK
Telegram campaign inside the same numbering: "5-error -> rc=0 parity proven
(ROOT-064..067 recorded with diffs in comments); G21 seven AOSP measure laws; login
text ink + z-order overpaint frontier honestly open; Dialogs-page first render
recorded; full main-UI NOT achieved."

**This discrepancy is preserved, not papered over**: the worklog's S117–S119 sections
do not record the official-APK Telegram work; the ledger locates it in #356 comments
(diffs + run tables), which are on GitHub but are **not** repo files. Both records are
stated; they are not merged.

---

## 3. STATUS — RESULT — EVIDENCE rows

Status vocabulary is the forensic-ledger set: `VERIFIED / TESTED / OBSERVED / PARTIAL /
PENDING / BLOCKED / SUPERSEDED / UNVERIFIED_CLAIM / REGRESSED`. No bare "DONE".

### 3.1 Provenance and window rows

**R01 — Journey document published as an external preview download**
- STATUS: `UNVERIFIED_CLAIM`
- RESULT: Preview host dead; markdown never committed; content survives only in issue
  comments. This file is the reconstruction of that missing artifact from preserved
  repo evidence — original wording unrecoverable.
- EVIDENCE: `FR-NI-006` (E0); FORENSIC_UNVERIFIED_CLAIMS §U1; FORENSIC_MISSING_EVIDENCE
  §M2; worklog forensic wave; empty git history for this path.

**R02 — S117 scope was complete-graphics, Telegram as named open frontier**
- STATUS: `OBSERVED`
- RESULT: Six generic laws (RFC 3986 §5.2.4 dot-segments; WHATWG DOM traversal family;
  CSS calc() nested min/max/clamp; flex-shrink; SVG2 inline rendering
  path/use/symbol/viewBox/fill/stroke; SVG layout integration). Open frontiers include
  verbatim "Telegram login pixels (R$styleable/text-draw)".
- EVIDENCE: `worklog.md` S117 (Work Log + Stage Summary); commits `c3b9fcb3`, `45a6b011`.

**R03 — S118 directive explicitly deprioritized Telegram**
- STATUS: `OBSERVED`
- RESULT: "Telegram deprioritized for now; complete EVERY incomplete app/game…" —
  eleven generic laws, zero Telegram-targeted (HTML5/WebView engine laws, not the
  dalvik view pipeline). Wave report itself says "Telegram deprioritized per directive".
- EVIDENCE: `worklog.md` S118; commit `09f5000f` message; `scripts/s118_post_comments.py`
  docstring/body.

**R04 — S119 directive: native games; Telegram deprioritized again**
- STATUS: `OBSERVED`
- RESULT: "focus on dooz (Tic-Tac-Toe) and other NON-HTML5 native games". Stage summary
  closes: "(deprioritized per directive) Telegram frontier + HTML5 weather forecast /
  accelerace car visibility".
- EVIDENCE: `worklog.md` S119 (Task line + Stage Summary).

### 3.2 S117 Telegram-facing rows

**R05 — S117 forkgram createView disassembly probe (the "fragment/createView disasm")**
- STATUS: `OBSERVED`
- RESULT: S117 code commit described as "fragment/createView disasm + scene work".
  Preserved artifact `scripts/s117_disasm_createview.py`: dalvik disassembler probe over
  `upload/tg/forkgram.apk` targeting `Lorg/telegram/ui/nr1;.createView` "around pc=120
  (the Space addView site) + list all addView call sites with their arg counts and
  preceding LP construction, to pin the exact addView overload used." Script committed;
  **no committed output/log exists** (gap G2).
- EVIDENCE: `scripts/s117_disasm_createview.py` (docstring quoted); `worklog.md` S117.

**R06 — S117 battery gates byte-identical to the S114 baseline (zero drift)**
- STATUS: `TESTED`
- RESULT: 4 HTML5 apps + 2 native gates at the fresh binary. Gate sha16s, source-pinned
  in `evidence/s117_complete_graphics/summary.json` and matching the worklog:
  blockbuster `05cd9f35ca005959`, mykanji `16d5fc1ebdaabaa4`, ballbreak
  `25e7219086a5654d`, dooz `84c6d4a59597e7f6` — "ALL byte-identical to the S114
  baseline (zero drift through every new law)". (dooz gate here: rc=1, 32 errors,
  NEAR_BLANK — its playable state arrives in S119.)
- EVIDENCE: `evidence/s117_complete_graphics/summary.json` (exact sha16 fields);
  `worklog.md` S117 BATTERY bullet.

**R07 — S117 wave results (non-Telegram, carried for window honesty)**
- STATUS: `PARTIAL`
- RESULT: weather NEAR_BLANK (0.23% non-bg) → real UI (nav icons painting, ControlView
  js_errors=0), honestly PARTIAL — body content still needs fetch/crypto.subtle/
  geolocation chain; accelerace 29→40 5-bit colors; blockbuster/mykanji anchors
  byte-stable. No Telegram claim beyond R02/R05.
- EVIDENCE: `worklog.md` S117 RESULTS; `evidence/s117_complete_graphics/summary.json`
  (render_verdicts); commit `c3b9fcb3`.

### 3.3 S118 rows

**R08 — S118 eleven generic laws (complete-the-incomplete)**
- STATUS: `TESTED`
- RESULT: QuickJS job pump ("without it NO promise ever resumed"); fetch()+Response over
  the S100 NET-001 HTTPS client; crypto.subtle.digest (OpenSSL EVP) + TextEncoder/
  TextDecoder; SVG shape getBoundingClientRect; SVG intrinsic-ratio width (SVG2 7.2);
  flex-direction ROW default; justify-content:center main-axis; flex cross-axis
  stretch; invalid-at-computed-value-time var() rule; :nth-child an+b grammar; forced
  sync layout + SVG stroke-width CSS-length resolution + box-shadow calc tokenizer +
  querySelector subtree scoping. All generic, zero package checks.
- EVIDENCE: `worklog.md` S118 (laws 1–11 enumerated); commit `09f5000f` message.

**R09 — S118 results: accelerace scene rendered; weather first real HTTP round-trip**
- STATUS: `TESTED`
- RESULT: accelerace blank → RENDERED scene (centered road strip 460px @x=310, street
  lights, score, road_lines animating; car SVG strokes paint 14.9M px but car still not
  visible in capture — stacking subtlety honestly open); weather → live TLS GET to
  isengard.su API, HTTP 200, 7023 bytes, city "Moscow" rendered from the response.
- EVIDENCE: `worklog.md` S118 RESULTS; `evidence/s118_complete/accelerace_scene.jpg`,
  `weather_moscow_live.jpg`.

**R10 — S118 native gates byte-identical; two anchors lawfully re-baselined**
- STATUS: `TESTED`
- RESULT: ballbreak `25e72190` and dooz `84c6d4a5` byte-identical (native untouched);
  blockbuster `05cd9f35` → `901818a0` and mykanji `16d5fc1e` → `adb5719` re-baselined
  by the corrected CSS laws ("documented, layouts improved").
- EVIDENCE: `worklog.md` S118 GATES bullet (sha16s as quoted); commit `09f5000f`.

**R11 — S118 Telegram delta: none (explicitly)**
- STATUS: `OBSERVED`
- RESULT: No Telegram-specific law, run, or evidence item in S118. Open-frontier list:
  accelerace car visibility, weather forecast rows, native appcompat menu-inflater NPE,
  empty-view-tree family (~43), libGDX .so family.
- EVIDENCE: `worklog.md` S118 Stage Summary; `scripts/s118_post_comments.py` wave body.

### 3.4 S119 rows

**R12 — dooz (Tic-Tac-Toe) flagship full agent-vs-phone game, 3-run byte-identical**
- STATUS: `TESTED`
- RESULT: S83 vision-driven driver at current HEAD: X opening, AI replies, yellow win
  strike, "Phone wins! Score x 0 : 1" dialog, NEXT ROUND → round 2 with scoreboard
  preserved. 3 independent full runs → all 4 stage frames byte-identical
  (VERIFIED_3RUN, S100 §25).
- EVIDENCE: `worklog.md` S119 first bullet; `evidence/s119_games/ttt1_opening_x_o.png`,
  `ttt2_win_and_dialog.png`, `ttt3_round2_score_kept.png`.

**R13 — Stale-driver-geometry family root-caused; vision-recalibrated, never re-hardcoded**
- STATUS: `TESTED`
- RESULT: S80/S98 hard-coded taps/rects missed the current render (layout laws
  evolved): snake never pressed START (tap y1500 vs button y1330); 2048 board_top()
  109px off (driver simmed "score~248" while HUD showed 4). Fixed via runtime pixel
  probes (s80_sd START/BTN rows, s80_tet control rows, s80_2048 `measure_board_top`).
- EVIDENCE: `worklog.md` S119; `scripts/s119_calibrate.py`/`_2.py`/`_3.py` docstrings
  ("measure CURRENT button geometry from rendered frames… vision-derived").

**R14 — Post-recalibration HUD-anchored gameplay results**
- STATUS: `OBSERVED`
- RESULT: 2048 SCORE 84 (16/8/8 merges); snake_deluxe SCORE 2/BEST 2 (driver AI not
  wrap-aware — honest open); tetris 7 locks + 10-piece stack (strict driver-model abort
  documented); minicraft PASS (cottage 113190 roof ink); snake_neon HUD score=10 len=4
  at frame 124.
- EVIDENCE: `worklog.md` S119; `evidence/s119_games/` (8 PNGs, 460px, 26–66 KB).

**R15 — S119 packaging, commit, wave report**
- STATUS: `OBSERVED`
- RESULT: 8 evidence PNGs in `evidence/s119_games/`; committed+pushed `34f462e6`
  (secret guard PASS); S119 wave report on #354 (comment 5894337102). Telegram
  untouched in S119.
- EVIDENCE: `worklog.md` S119; `evidence/s119_games/` (8 files verified present);
  commit `34f462e6`.

### 3.5 Official Telegram S117→S119 campaign (ledger-recorded; repo artifacts absent)

**R16 — Official Telegram campaign: 5-error → rc=0 parity (issue #356)**
- STATUS: `PARTIAL`
- RESULT: Per FR-356: "5-error -> rc=0 parity proven (ROOT-064..067 recorded with diffs
  in comments); G21 seven AOSP measure laws; login text ink + z-order overpaint
  frontier honestly open; Dialogs-page first render recorded; full main-UI NOT
  achieved." Acceptance criteria (official APK 0-error execution; login pixels; main
  UI) NOT fully met — main UI explicitly not achieved. Level E4; the row's
  `commit_shas` list is **empty** (gap G1).
- EVIDENCE: `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl` row `FR-356` (quoted). No
  repo-committed run log/screenshot/diff for ROOT-064..067 exists (verified, §5).

**R17 — ROOT-064..067 + G21 exist in NO registry**
- STATUS: `BLOCKED` (registry coverage gap, recorded)
- RESULT: The Telegram-chain roots behind the official campaign live only in issue
  comments/worklog. Re-verified during this reconstruction: **zero hits for
  ROOT-062…ROOT-067** in `root_registry.json` (530 roots) and in the canonical
  projection `canonical/root_cause_registry.json` (492). Until registry rows with
  commit+trace refs exist, those roots stay TESTED/OBSERVED at E3/E4, never VERIFIED.
- EVIDENCE: FORENSIC_UNVERIFIED_CLAIMS §U2; FORENSIC_MISSING_EVIDENCE §M1; ledger
  `FR-NI-007`; reconstruction-time string search of both registry files.

**R18 — The 190-goal Telegram roadmap: 18/190 checked**
- STATUS: `PARTIAL`
- RESULT: "TELEGRAM 190-GOAL ROADMAP — full execution & display ladder (19 phases)"
  (#356 comment 4 + #363 §3): G1–G18 checked = environment + official-parity waves;
  ROOT-064..067 + G11–G17 carry diffs/run tables in #356 comments (E4); G19–G190 (172
  goals) UNCHECKED = PENDING by design. Per #365 §11 ("do not trust checked boxes")
  all 18 checked goals audited to OBSERVED (E3), not VERIFIED; G2's rebuild was
  independently reproduced at HEAD during the forensic campaign; the rest NOT
  re-executed.
- EVIDENCE: ledger `FR-NI-003` + rows `FR-NI-003-G1..G18` (all OBSERVED/E3).

**R19 — Knowledge-transfer series 1/7 … 7/7 (issues #357–#363)**
- STATUS: `VERIFIED` (as issue-body documentation, level E2)
- RESULT: Seven deliverables — master index; wave 1 (official Telegram from first-ever
  run (5 errors) to rc=0 — four root causes, forensics, code anchors); wave 2 (the G21
  autopsy and seven AOSP measure laws — the login tree comes on-screen); wave 3 record
  with attribution + fresh-run proof; six reproduction scripts + forensic probe kit;
  complete session engine diff; 190-goal roadmap + regression-gate method + honest
  frontier. VERIFIED **only as issue-body documentation**: "External preview link
  inside #356/#355 comments is DEAD (preview host) — content preserved in the issue
  text; the journey markdown was never committed to the repo."
- EVIDENCE: ledger `FR-357`…`FR-363` (all VERIFIED/E2); §U7 + §M10 (the six-scripts
  1:1 mapping is itself PARTIAL until cross-checked).

**R20 — Pinned re-execution protocol `scripts/s117_tg_run.sh` is missing**
- STATUS: `PENDING`
- RESULT: §U3 pins re-execution as "current HEAD under the pinned protocol
  (`scripts/s117_tg_run.sh`)"; §M3 asks for "fresh `scripts/s117_tg_run.sh
  official|forkgram` runs at current HEAD". The file is **not present** in `scripts/`
  today (verified; only s117 scripts are `s117_complete_graphics.py` and
  `s117_disasm_createview.py`). The S117 official-APK anchors were recorded on a
  different sandbox and are not re-runnable from the repo as-is (gap G3).
- EVIDENCE: FORENSIC_UNVERIFIED_CLAIMS §U3; FORENSIC_MISSING_EVIDENCE §M3;
  reconstruction-time listing of `scripts/`.

**R21 — G18's committed official-APK inventory file was never located**
- STATUS: `PENDING`
- RESULT: G18's inventory "is referenced but the committed inventory file was not
  located by this audit"; G19 login-path resource enumeration unchecked by design.
- EVIDENCE: §U3; §M4.

### 3.6 forkgram committed evidence chain (the repo-verifiable backbone)

**R22 — forkgram run progression S108 → S115 (errors 32 → 7 → 6 → 0)**
- STATUS: `TESTED`
- RESULT: S108: first SUCCESS-path run, errors 32→7, view tree LaunchActivity$w →
  DrawerLayoutContainer → ActionBarLayout → a4. S109: roots 027–045, REAL LOGIN UI tree
  (ScrollView → he1$a 6 children → he1$d "StartMessaging" button measured 1080x48
  @y1656, ViewPager, TextureView, 30+ nodes), residual 6 errors. S110: ROOT-046
  KeyStore family + ROOT-047 getBaseContext → **0 errors, crash.log empty, first
  zero-error forkgram run**. S115: ROOT-062 (AOSP CREATED-PHASE lifecycle fan-out;
  Recreator "Next event must be ON_CREATE" AssertionError) + ROOT-063
  (StaticLayout$Builder materialization) → **first fully clean execution (rc=0,
  0 errors, 0 warnings, 0 uncaught)**, StartMessaging text resolved and set.
- EVIDENCE: `evidence/s108_telegram/`; `evidence/s109_telegram/run1..run2` (reports +
  full logs; run1 report lists the exact 6 NPEs incl. FingerprintController.
  checkKeyReady ×2 and 2× APP-BOUNDARY at LaunchActivity.onCreate);
  `evidence/s110_telegram/fix44_zero_errors/report.md` (Status SUCCESS, Errors 0);
  `evidence/s115_telegram/REPORT.md` (run table run2→run4, 4→3→0 uncaught); commits
  `8acc8a24`, `a86f7d47`, `fc1d9f05`, `7ca4e350`, `6a61875f`.

**R23 — forkgram deterministic themed window SHA-256 `59fdbfcd60b86a23…`**
- STATUS: `TESTED`
- RESULT: Worklog pins "Telegram run1/run2 deterministic themed window 59fdbfcd…".
  At reconstruction time the full SHA-256 of **all eight committed capture copies**
  (`evidence/s108_telegram/screenshot.png`, `evidence/s109_telegram/run1|run2/
  screenshot.png`, `evidence/s110_telegram/fix44_zero_errors/screenshot.png`,
  `evidence/s115_telegram/run2|run3|run4/screenshot.png`) was recomputed: every copy
  byte-identical, SHA-256
  `59fdbfcd60b86a23f24b6d678e2e80c48d349dbbb71028ca9ec0ee00993c298d` — consistent with
  the source pin (first 16 hex). One byte-identical frame across S108→S115 is itself
  the record: **the committed forkgram window never gained pixels** (R26/R27).
- EVIDENCE: `worklog.md` S109 ("forkgram 59fdbfcd deterministic x2"); SHA-256 recomputed
  over the 8 committed files (hashlib.sha256).

**R24 — forkgram reference screenshot SHA `a96f6a13…` (S82 registry pin)**
- STATUS: `OBSERVED`
- RESULT: `evidence/s108_telegram/reference_forkgram.png` recomputed SHA-256
  `a96f6a138f7129ccbcdf093c0d249ad10de50c55d0ff89c96c3cfce8431c130d`, matching the
  worklog pin "reference_forkgram.png SHA a96f6a13... matching the s82 registry pin".
- EVIDENCE: `worklog.md` S108 EVIDENCE bullet; reconstruction-time recompute.

**R25 — forkgram golden `bbb6cd10a834963d` in campaign store gates**
- STATUS: `TESTED`
- RESULT: Golden frame sha16 `bbb6cd10a834963d` recorded in the installed-state gate
  ("telegram bbb6cd10a834963d ×3" == golden, source-APK hidden, 22 runtime-created
  files under data/data/<pkg>) and in FR-355 ("golden bbb6cd10a834963d recorded in
  campaign gates; NOT re-run at HEAD during this forensic pass"). Later
  DIFFERENTIAL-era note: the golden drifted from the V10 value `cf4c41e62ceb6557`
  after F-NEW-226/227 text laws changed text pixels (REAL_APP_CONTENT verdict; F-016
  ×6 uncaught) — recorded, not hidden.
- EVIDENCE: `worklog.md` §9/§ST rows; `CAMPAIGN_STATE.md` (installed-state gate lines);
  ledger `FR-355`; `worklog.md` MEGA-W2 regression-set row.

**R26 — forkgram pixel state at the S117 carry-in: measured, NOT painting**
- STATUS: `OBSERVED`
- RESULT: `evidence/s115_telegram/REPORT.md` §21, verbatim: "forkgram execution:
  EXECUTED, VERIFIED 0-error (deepest ever: StartMessaging button text resolved and
  set on the login view…)" and "forkgram pixels: **NOT RENDERED YET** — the login tree
  is measured but not painting (R$styleable theme attrs + text-draw laws = the known
  pixel frontier, unchanged)". This is the exact frontier S117 names open (R02).
- EVIDENCE: `evidence/s115_telegram/REPORT.md` (§21 + Next frontier).

**R27 — Post-window forkgram pixel proof (context, after S119)**
- STATUS: `OBSERVED`
- RESULT: Later differential-era session: "forkgram cf4c41e62ceb6557 x3 =
  REAL_APP_CONTENT (OBSERVED): 31 nodes depth 7, app_draw_ops 11, app pixels 117,133
  INSIDE bounds, chrome 0, 204 colors (theme bg #e1e1e1 + white cards + #85caff
  accents), inflation_failed=false — first Telegram-class flagship with in-bounds
  proof." Post-dates the window; recorded to bound what the frontier later became —
  not claimed as an S117–S119 result.
- EVIDENCE: `worklog.md` differential wave (forkgram in-bounds proof row).

### 3.7 Honesty-law rows (grey frame = load frontier, NOT render)

**R28 — The grey-frame honesty law for Telegram**
- STATUS: `OBSERVED`
- RESULT: S124 (per directive "never claim games/apps are 100% rendered"), verbatim:
  "HONESTY GATE per directive: Telegram 48f last frame = 3 grey colors -> labeled NOT A
  RENDER (SvgHelper themed-icon SVG parsing runs ~24M+ instrs; 8 uncaught, same-config
  A/B parity with the pre-S124 binary; S123's 47-uncaught was a longer-run artifact)."
  S123 quantified the load side: "LaunchActivity dispatches, onCreate proceeds past its
  catch-alls to invoke_pc 548+; blocker quantified (LocationController gms
  getImpliedScopes NPE ×6, 47 uncaught); frame pre-pixel". The grey frame proves
  **how far loading got**, never that anything rendered.
- EVIDENCE: `worklog.md` S123/S124; `canonical/app_registry.json` checkpoint_law:
  "Telegram/WhatsApp are honest BLOCKED load frontiers — their frames are NOT renders."

**R29 — Official Telegram registry state (canonical, current truth)**
- STATUS: `BLOCKED`
- RESULT: `canonical/app_registry.json` APP-012 "Telegram 12.10.1"
  (`org.telegram.messenger`): BLOCKED; checkpoints L0/L1/L2 true, **L3 (view tree)
  false**; note verbatim: "LaunchActivity dispatches deep (invoke_pc 548+); frame = 3
  grey colors -> NOT A RENDER (honest); frontier: SvgHelper themed-icon SVG parsing +
  gms Api builder nulls"; evidence_ref
  `evidence/s124_theme_base/s124_telegram1_grey_frontier.jpg`. Later gates unchanged:
  "telegram/whatsapp honest NOT-A-RENDER frontier unchanged (3/2 colors, 8 uncaught)"
  (S127/S128/S129 input waves).
- EVIDENCE: `canonical/app_registry.json` APP-012; `worklog.md` S127/S128/S129
  verification bullets.

**R30 — Official Telegram, pre-window MC4 baseline (v12.10.1, SHA-pinned)**
- STATUS: `PARTIAL`
- RESULT: `docs/evidence/mc4_telegram/EVIDENCE.json`: run1 rc=1, 1 frame, full-screen
  themed window painted (frame SHA-256 `6da8020bfcb07fb3390b487a7dd97882dc27127b25cf04c
  300a98cd9aa0ae379`, pinned in `SHAS.txt`), died in ImageLoader LruCache
  IllegalArgumentException ×62 (getMemoryClass unimplemented → 0); run2 (post
  getMemoryClass=256 fix) rc=124 timeout at 570s = **progress, not
  crash-at-same-point** (ImageLoader IAE eliminated; new blocker j$/util/stream
  "called wrong accept method" ×191 via MessagesController/ConnectionsManager
  getInstance). Classification verbatim: "REAL APK FRONTIER — not claimed usable".
- EVIDENCE: `docs/evidence/mc4_telegram/EVIDENCE.json` + `SHAS.txt` +
  `tg_run1_distilled.log` / `tg_run2_distilled.log`.

**R31 — Official Telegram, post-window settings-face record (context)**
- STATUS: `PARTIAL`
- RESULT: Later random-selection session: "telegram_official.apk launches (F-016 ×4) —
  final face = REAL Telegram settings activity ('LowPowerEnabledTitle' doubled text +
  'Disable'), same sha as forkgram (both land on the same settings face). NOT the main
  UI; NOT marked success. First missing laws = intro/auth navigation chain +
  title-overlap layout bug." Ledger FR-016 ([EXEC] Telegram — Runtime Compatibility):
  "0-error runs + settings face recorded; main UI NOT reached (intro/auth chain open)"
  — PARTIAL/E4.
- EVIDENCE: `worklog.md` MEGA-W2 §6 row; ledger `FR-016`; `CAMPAIGN_STATE.md`
  checklist row 9 (title-overlap + intro/auth chain REGISTERED; installed-mode
  filesystem RULED OUT as cause via F-NEW-234 file-IO trace).

---

## 4. The honest state of Telegram at the end of the S117→S119 window

1. **Execution vs render are different claims.** forkgram reached a verified 0-error
   execution (rc=0) with the real login view tree built and StartMessaging text set
   (R22/R26) — while its committed frame stayed one byte-identical themed window
   (`59fdbfcd…`, R23). The official APK (FR-356) reached rc=0 parity with a
   Dialogs-page first render recorded in comments, but "full main-UI NOT achieved" and
   "login text ink + z-order overpaint frontier honestly open" (R16). No repo evidence
   supports a "Telegram renders" claim.
2. **A grey/blank/single-themed frame is a LOAD measurement, not a RENDER.** The
   canonical registry hard-codes it: Telegram/WhatsApp frames "are NOT renders" (R28);
   the 3-grey-color frame is labeled NOT A RENDER with the blocker named (SvgHelper
   themed-icon SVG parsing + gms Api builder nulls, R29).
3. **Official ≠ forkgram.** Every repo-committed Telegram run artifact in/around the
   window is forkgram `3baeecb3`-pinned; the official-APK S117→S119 campaign survives
   only as #356 comment diffs/run tables summarized by FR-356 (R16) plus the
   SHA-pinned official MC4 baseline (R30).
4. **Frontier after the window** (orientation only, post-window records): official =
   intro/auth navigation chain + title-overlap layout bug + SvgHelper/gms frontiers
   (R29/R31); forkgram = first REAL_APP_CONTENT in-bounds proof at a later HEAD (R27).

---

## 5. Evidence gaps found during reconstruction

- **G1 — No committed official-APK S117→S119 run artifacts.** FR-356 has an empty
  `commit_shas` list; no run log/screenshot/diff for ROOT-064..067 / G21 in `docs/`,
  `evidence/`, or `run/`. Evidence available in this reconstruction: the FR-356 ledger
  row text only.
- **G2 — `scripts/s117_disasm_createview.py` has no committed output.** The probe
  script survives; its findings (exact addView overload at the forkgram `nr1.createView`
  Space site) were not committed. Evidence available: the script's docstring only.
- **G3 — `scripts/s117_tg_run.sh` (pinned re-execution protocol) absent** from
  `scripts/`, though §U3/§M3 cite it. S117 official-APK anchors not re-runnable from
  the repo as-is.
- **G4 — ROOT-062..067 + S102-A..D in no registry** (verified: zero hits in
  `root_registry.json` and `canonical/root_cause_registry.json`).
- **G5 — G18's official-APK inventory file** never located in the repo (§U3/§M4).
- **G6 — `run/s11*` manifests do not exist**; `run/` has no s11x directories (only
  s100/s83b/s88/s94/user_goldens/audit/diff366/forensic_uninstall_store). Raw runs
  referenced by committed reports (e.g. `run/s110_tg/fix44/screenshot.png` inside
  `evidence/s110_telegram/.../report.md`) are gone; only packaged smalls under
  `evidence/` remain.
- **G7 — The three context docs are thin on Telegram:** `docs/S102_REPORT.md` — zero
  Telegram mentions (Compose-family sweep); `docs/REAL_ANDROID_LOADING_ORACLE.md` —
  zero Telegram mentions (AOSP law oracle); Telegram appears only in
  `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md` (ZIP self-access law "tested Telegram";
  file-IO trace 185 ops telegram r1; ST-4 `/dev/urandom` raw-host-path OPEN; 7
  provenance-checked asset OPENs; telegram `bbb6cd10a834963d` determinism row);
  `docs/FORENSIC_EVIDENCE_INDEX.jsonl` (52 artifacts) — zero Telegram rows.
- **G8 — Worklog S117–S119 vs #356 discrepancy** (see §2): the official-APK campaign is
  not in the worklog; both records preserved as-is, no reconciliation possible from
  repo evidence.
- **G9 — Original wording unrecoverable.** Nothing in the repo preserves the lost
  markdown's structure or prose; issue-comment texts are on GitHub (ledger-referenced)
  but are not repo files and were not fetched here.

---

## 6. Source index

- `worklog.md` — S107–S111, **S117, S118, S119**, S123–S124, S127–S129, MEGA-W2,
  forensic wave, differential wave sections (Telegram rows quoted above).
- `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl` — 13 Telegram/S11x-matched rows parsed
  programmatically: FR-001, FR-016, FR-349..352, FR-355..363, FR-NI-003 (+G1..G18),
  FR-NI-006, FR-NI-007; quoted fields verbatim.
- `docs/FORENSIC_UNVERIFIED_CLAIMS.md` (§U1–U3, U7); `docs/FORENSIC_MISSING_EVIDENCE.md`
  (§M1–M4, M10); `docs/FORENSIC_VERIFIED_WORK.md` (no Telegram/journey rows — checked).
- `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md`; `docs/S102_REPORT.md` +
  `docs/REAL_ANDROID_LOADING_ORACLE.md` (no Telegram content — gap G7).
- Evidence dirs: `evidence/s108_telegram/`, `s109_telegram/` (run1/run2 reports +
  traces), `s110_telegram/`, `s115_telegram/` (REPORT.md + run2–4),
  `docs/evidence/mc4_telegram/` (EVIDENCE.json, SHAS.txt, distilled logs),
  `evidence/s117_complete_graphics/` (summary.json + 6 app reports),
  `evidence/s118_complete/`, `evidence/s119_games/`. (`docs/evidence/s108_telegram/`
  etc. do not exist; Telegram evidence lives at the repo-root `evidence/` tree.)
- Scripts: `s117_complete_graphics.py`, `s117_disasm_createview.py`,
  `s118_post_comments.py`, `s119_calibrate{,2,3}.py`, `s119_package.py`.
- Registries/state: `canonical/app_registry.json` (APP-012/013 + checkpoint_law),
  `canonical/root_cause_registry.json` + `root_registry.json` (ROOT-062..067 absence),
  `CAMPAIGN_STATE.md`.
- Git: log for this path (empty); S117–S119 commits `45a6b011`, `c3b9fcb3`, `09f5000f`,
  `34f462e6`; Telegram-chain commits `8acc8a24`, `a86f7d47`, `fc1d9f05`, `7ca4e350`,
  `6a61875f`, `9f986e1c`.

*End of reconstruction. STATUS vocabulary per `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl`
(#365 §2). No result in this document may be quoted without its row's EVIDENCE line.*
