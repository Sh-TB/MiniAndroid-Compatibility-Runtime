> **[S87 SUPERSEDED]** Era record — do not update. Current canonical achievement record: [`docs/ACHIEVEMENTS.md`](../ACHIEVEMENTS.md) (generated from [`docs/evidence/canonical/registry.json`](canonical/registry.json), the Single Source of Truth; see also [canonical/](canonical/)). Earlier supersession pointer to EXECUTION_ACHIEVEMENTS.md is itself superseded since S54.

# SCREENSHOT_INDEX_S51 — ALL-FRONT STATUS AUDIT (curated gallery + per-app truth)

Campaign: S51 FINALIZATION — all-front attack on every work-list app.
Date: 2026-09-17 · Local HEAD: `1b37afd1` (== remote main, REMOTE VERIFIED) ·
runtime rebuilt from canonical tree (`make -j2`, BUILD_ID = HEAD) ·
regression battery: **ALL PASS 92/92 stages** at this HEAD
(`scripts/test/run_test_battery.sh --resume`; historical "94/94" = pre-purge
script revision with 2 extra sub-stages — current canonical count is 92).

Status vocabulary (§42, unchanged): VERIFIED / PARTIAL / BLOCKED / NOT_TESTED +
budget notes. Nothing upgraded without runtime evidence at this HEAD.

## 1. Battery-verified core gate (fresh at this HEAD)

| Stage chain | Verdict | Evidence |
|---|---|---|
| make build + resource_trace | PASS | BUILD_ID = `1b37afd1` |
| semantic battery (long/cmp/conv/bridge/switch) + MUTF-8 (7/7) | PASS | battery state dir |
| helloworld_golden §28 (18 checks) | PASS | /tmp/battery_* run trees |
| tictactoe_golden §29 (interaction 9/9 + determinism) | PASS | "X→O→X WINS" chain |
| EXT-01/02 HelloWorldSelfAware (APK SHA `009b4671…` hash-verified re-fetch) | PASS | typography 9 + interaction 12 checks |
| G04 density oracle · G06/G07/G08 toolchain fixtures + 3-run determinism | PASS | aapt2+ECJ+D8 builds re-bootstrapped via scripts/build/bootstrap_toolchain.sh |
| M3 ARSC/style chain · F-012/016/020/024/025/026/027/028/030/040/044/050/074 laws | PASS | every fixture rebuilt + pixel goldens |
| corpus runs: simplestopwatch, gmdice, microtimer | PASS | hash-verified APKs |

## 2. Fresh per-app runs at this HEAD (the work list, app by app)

Gallery: `docs/evidence/s51_audit/*.jpg` (540x960 q72, all ≤100 KB; full SHA256
in `docs/evidence/s51_audit/SHA256SUMS`). PNG frame SHAs are the fine-grained
determinism anchors; run trees in `/tmp/s51_audit/<app>/` (external, untracked).

| # | App | Verdict (this HEAD) | Frame PNG SHA-16 | Gallery | Classification |
|---|-----|--------------------|------------------|---------|----------------|
| 1 | chessclock | **SUCCESS** rc=0 | `e4a2d7c90cd2fd26` | chessclock.jpg | full run |
| 2 | unote | **SUCCESS** rc=0 | `7b30d52201bb22ac` | unote.jpg | full run |
| 3 | bouncy | **SUCCESS** rc=0 | `4219c5116ea2a867` | bouncy.jpg | full run |
| 4 | headingcalculator | **SUCCESS** rc=0 | `293b6761e46fba35` | headingcalculator.jpg | full run |
| 5 | notes (billthefarmer) | **SUCCESS** rc=0 | `ae697935dbeb6f33` | notesbillthefarmer.jpg | full run |
| 6 | microtimer | **SUCCESS** rc=0 | `c51269309cd14594` | microtimer.jpg | full run |
| 7 | simplekeyboard | SUCCESS rc=0 (default screen — IME, no launch UI) | `eb16ab5c68fa9b6c` | simplekeyboard.jpg | input-method boundary |
| 8 | RTTT (kirkezz) | SUCCESS rc=0 (default screen; Compose family) | `eb16ab5c68fa9b6c` | rttt.jpg | Compose frontier family |
| 9 | dooz v18 | **PARTIAL — R-NEW-361 signature REPRODUCED**: `[HALT-LOOP] Lh/r;.c PC=0x1c 50001 visits` + `aput-oob length=7 index=613985991 LP/v$a;.c pc=28` | `31ddd4d5b8e6d18e` | dooz18.jpg | open root (OBSERVED-FAIL, registry-honest) |
| 10 | dooz v23 | **PARTIAL — deterministic pipeline completion** (same frame SHA as S41-era ×4 runs); F-016 honesty now surfaces 1 uncaught in-flight exception (7 unwind entries = R-NEW-344 refined chain; was pre-honesty "0 errors" accounting) | `31ddd4d5b8e6d18e` | dooz23.jpg | content-composition frontier |
| 11 | tictactoe (emmanuelmess) | PARTIAL — blank first frame (Compose/libGDX family) | `31ddd4d5b8e6d18e` | tictactoe_corpus.jpg | Compose frontier family |
| 12 | stopwatch (muellerma) | PARTIAL — manifest has NO launchable Activity (QuickSettings Tile app) | `eb16ab5c68fa9b6c` | stopwatchmuellerma.jpg | documented §18 boundary |
| 13 | BGClock (hansdezwart) | PARTIAL — WebView root node (clock face is HTML/JS) | `2f85dd74aa54e463` (EXACT u013 match) | bgclock.jpg | documented §19 boundary |
| 14 | itsfrz tictactoe | PARTIAL — NPE at app boundary | `eb16ab5c68fa9b6c` | itsfrz.jpg | app-code boundary |
| 15 | Privacy Friendly Dicer | PARTIAL — ISE at app boundary | `eb16ab5c68fa9b6c` | secuso_dicer.jpg | app-code boundary |
| 16 | OpenLauncher | PARTIAL — heavy launcher, default screen | `eb16ab5c68fa9b6c` | openlauncher.jpg | app-code boundary |
| 17 | simple_flashlight | PARTIAL — default screen | `eb16ab5c68fa9b6c` | flashlight.jpg | app-code boundary |

Shared-frame honesty: `31ddd4d5…` = the deterministic blank Compose frame;
`eb16ab5c…` = the deterministic default/entry screen. Identical SHAs across
apps are the expected signature of these two known render classes, NOT copy
errors.

## 3. Did NOT reach first frame this session (honest frontier)

| App | This session | Historical standing |
|---|---|---|
| Telegram v12 (APK SHA `f5e11927…` verified) | 540 s budget consumed INSIDE real init — 989k log lines, androidx SafeIterableMap cycle-stub at 18k+ calls, 400 REC-MISS; no frame yet | golden login-stall frame `088ea640…` (41,233 px) stands at its recorded campaign HEAD |
| Antimine | killed at 300 s (no status line) | registry: runs to MainActivity.onCreate, ISE at boundary |
| Secuso memory / sudoku | >300 s each (killed) | NOT_TESTED at this HEAD |
| Secuso 2048, Lexica | not re-run | registry: EXEC BUDGET TIMEOUT (540 s heavy apps) |
| solitaire, braincup, droidify, s37 family (minesweepers/sudoku/2048 variants/word game) | not re-run this session | campaign014/u011-era sheets stand |
| WhatsApp | APK not in external cache → not re-runnable | u011_3 probe evidence stands (entry chain + typed catches + LX/0F7 stall) |

## 4. Provenance

- Runs: `./build/miniandroid run <apk> -o /tmp/s51_audit/<app>` at HEAD
  `1b37afd1`; battery state `/tmp/g09_battery_state` (92 `.pass`, zero FAIL).
- APK hashes: per `miniandroid/APK_REGISTRY.json` + EXT-01 re-fetch verified
  against `docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md` (both SHA256
  exact match).
- Toolchain re-bootstrapped this session from documented sources (aapt2
  8.13.2-14304508, ecj 3.33.0, r8 8.13.23, robolectric android-all-14).
- Historical galleries: `SCREENSHOT_INDEX.md` (§39 unified) and
  `SCREENSHOT_INDEX_013.md` (campaign-013) remain valid for their eras; this
  file supersedes them for CURRENT-HEAD status.
