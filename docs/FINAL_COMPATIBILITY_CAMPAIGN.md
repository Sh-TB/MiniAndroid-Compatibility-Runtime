# FINAL COMPATIBILITY CAMPAIGN — MASTER CHECKLIST

The ONE permanent master checklist (user directive §15). No competing checklist.
Created: 2026-10-02 · HEAD at creation: 286b4994 · Registry: 525 roots

Status legend:

```text
[ ] NOT STARTED     [~] IN PROGRESS    [?] OBSERVED
[✓] IMPLEMENTED     [✓✓] TESTED        [+] NEW APP SUCCESS
[!] REGRESSION      [X] BLOCKED        [S] SUPERSEDED
```

A checkbox becomes [✓✓] ONLY with runtime evidence. [+] ONLY when a real
previously-failing APK/game becomes successful. No evidence = no checkmark.

---

## LAWS READ (recorded 2026-10-02)

CONSTITUTION_V2 (source-first §2, never-invent-semantics §6, unknown-remains-unknown §7,
hypothesis≠root §8, fresh-live-evidence §9, first-divergence §16, silent-wrong §17,
register-width §21, R8-layer §22, end-to-end §26), MASTER ROADMAP, CAMPAIGN_STATE.md,
worklog.md (tail through F-NEW-228 completion wave), root_registry.json (525 roots,
status census), evidence laws (FRAME_CAPTURE_TRUTH 12-item proof chain),
FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT, F084 freeze, DEX register law,
class-init honesty (failed clinit → NCDFE), REC-MISS 7-class, no-package-specific-fixes,
bounded logging (S43 ring cap), screenshot/runtime proof laws (21-P0-6 pixel ownership),
APK hygiene laws (no APK/large binaries in git; tmp-only corpus artifacts),
installed-APK filesystem requirements (platform-audit Phases 5–8),
canonical/v10_results_latest.json (five-app gate), docs/corpus/s82/title_registry.json
(frozen corpus 202 titles: 100 game + 100 app + 2 mandatory), current README.md,
docs/ACHIEVEMENTS.md, docs/ROADMAP_STATUS.md, issue #354 checkpoint flow.

## CORPUS REALITY (§4 — do not trust old numbers)

- Frozen corpus: **202 titles** (100 GAME + 100 APP + 2 MANDATORY) in
  `docs/corpus/s82/title_registry.json` — NOT 255; older numbers (255/129) counted
  overlapping s107 run dirs. The s107 wave ran 129 unique titles from `/tmp/s107_apks/`
  which has been **purged from disk** (disk-hygiene law). No re-download.
- Locally present frozen-corpus APKs (the only honest random-selection pool):
  canonical 11 (dooz, microtimer, unote, bouncy, tictactoe, stopwatch, gmdice,
  fishrings, tripeaks, opmt, muellerma-stopwatch) + gates 9 (opencalc, forkgram,
  telegram_official, secuso notes, secuso sudoku, klondike, chess_jwtc, ballbreak,
  flappycow) + wave builds (g2048, snakedeluxe, tetris, ttt, minicraft, snakeneon,
  browsers, webfix).
- Random selection = deterministic seed over the local frozen pool; seed + pool
  recorded per iteration. Titles whose APKs were tmp-purged are UNTESTABLE-THIS-ENV
  (recorded, not hidden).

## MASTER CHECKLIST

### §1–2 Historical achievement audit (required legacy items)

| # | Item | Status |
|---|------|--------|
| 1 | F-NEW-221 R8 merged-class ctor/dispatch deep leg | [ ] |
| 2 | F-NEW-217 kotlinx resume protocol (dame leg) | [ ] |
| 3 | F-NEW-204..207 P1 audit batch | [ ] |
| 4 | F-NEW-192 | [ ] |
| 5 | secuso grey/white-face rendering/provenance | [ ] |
| 6 | §28 final deliverable refresh | [ ] |
| 7 | F-NEW-228 weight-pass (claimed DONE) — re-verify reproducible | [✓✓] opencalc e364b001ee7abd66 ×3 reproduced 2026-10-02 (plain AND from installed state) |
| 8 | F-NEW-229 CL MATCH_PARENT spec law | [ ] |
| 9 | F-NEW-230 golden provenance/config gap | [~] valid goldens re-banked with repro blocks; ssw/headingcalc/secuso/forkgram re-bank pending; whatsapp white golden rejected |
| 10 | Families A–W root/fan-out audit | [~] wave-2 established the deferred-UI fan-out family (fishrings/klondike/sudoku/chess/tripeaks/flappycow/ballbreak all pass through it) |
| 11 | Real-APK matrix refresh | [~] MEGA-W2 random ledger row 1 + regression battery banked |
| 12 | Installed-APK filesystem model proof | [✓✓] F-NEW-231 package store — 10/10 platform claims PASS |
| 13 | APK-inspection skill feasibility | [ ] |
| 14 | README/front-page audit | [ ] |
| 15 | Version/release audit + release candidate | [ ] |
| 16 | Registry/worklog/evidence reconciliation | [~] |

### §3 Installed-APK access (mandatory platform capability)

| # | Item | Status |
|---|------|--------|
| 1 | Gap audit: current install/discovery mechanism | [✓✓] gap confirmed (no install/list-packages/--package) |
| 2 | F-NEW-231 registered | [✓✓] |
| 3 | Generic `install` capability implemented | [✓✓] |
| 4 | Installed-package discovery (agent works from package identity alone) | [✓✓] |
| 5 | Manifest/DEX/resource inspection from installed state | [✓✓] analyze + dex on installed base.apk |
| 6 | Launch from installed state + provenance | [✓✓] lifecycle_trace apk=<store>/data/app/<pkg>/base.apk |
| 7 | APP proof (opencalc) ×3 runs | [✓✓] e364b001ee7abd66 ×3 (= golden) |
| 8 | GAME proof (bouncy) ×3 runs | [✓✓] b6dde6074bf47264 ×3 (real content, PARTIAL rc) |
| 9 | 10 platform claims answered | [✓✓] 10/10 PASS (registry F-NEW-231) |

### §4–5 Random corpus loop

| Iteration | Seed | Random APK 1 | Before | Root | After | Random APK 2 | Before | Root | After |
|----------:|------|--------------|--------|------|-------|--------------|--------|------|-------|
| MEGA-W2 | 20261002 | sudoku_secuso_101 (app, sha 1aff917f4ac9952b) | 31ddd4d5b8e6d18e WHITE (rc=0, false-SUCCESS pre-F-NEW-233) | F-NEW-232/233 + splash-Timer deferred UI | 45962e018344e94d ×3 (TutorialActivity + 2 buttons; text missing) | fishrings_v1.23_vc6 (game, sha 14d7dd80f7563c6a) | b5a7a35d5fe0564b flat #303030 | F-NEW-232 (splash Timer 5000ms never observed) | a341e3ad9092f640 ×3 REAL GAME BOARD |

### WAVE ENTRIES (§16 format)

```text
ID: F-NEW-231
DATE: 2026-10-02
ROOT: INSTALLED_APK_ACCESS — no install mechanism existed (only raw APK path)
SOURCE: AOSP PackageManagerService install law (android-14 /data/app commit,
        PackageInfo, /data/data app dirs)
LAW: install commits base.apk to the codePath; sourceDir = INSTALLED path;
     original sideload path not preserved; deterministic-mapping deviation
     documented for agent inspectability
BEFORE: `miniandroid help` has no install/list-packages/--package; sourceDir =
        sideload path; zero package store
CHANGE: package store in main.cpp — install (SHA-256 + integrity re-hash +
        PackageInfo-mirror package.json + /data/data dirs), list-packages,
        run --package (identity-only resolution)
AFTER: two-APK installed-state proof with source APKs physically hidden during
       the runs (moved to /tmp, restored after)
APK: opencalculator_53.apk (app) + bouncy.apk (game)
PACKAGE: com.darkempire78.opencalculator / com.dozingcatsoftware.bouncy
APK SHA: 2642613868a8a80f... / ffda0d9cb0b1b2aa...
RUN CONFIG: run --package <pkg> --data-root <store> -o <out> (defaults 1080x1920)
RUNTIME RESULT: opencalc ×3 rc=000 REAL_APP_CONTENT (297 colors, 64.7% button
       field + 34.5% display); bouncy ×3 real game content (145 colors pinball
       palette; PARTIAL rc, same face as sideload — not an installed-mode
       regression)
VIEWTREE/PROVENANCE: lifecycle_trace "apk" = <store>/data/app/<pkg>/base.apk in
       every run; sourceDir law satisfied
SCREENSHOT: evidence/f231_installed_access/{opencalc,bouncy}_from_installed_run1.png
SCREENSHOT SHA: e364b001ee7abd66 (opencalc = F-NEW-228 golden!) / b6dde6074bf47264
3-RUN: x3 byte-identical both APKs
NEW SUCCESS: platform capability (§3 10/10 claims PASS)
REGRESSION: none (goldens byte-identical)
COMMIT: (this wave)
ISSUE: #354
STATUS: IMPLEMENTED+TESTED
```

```text
ID: F-NEW-232
DATE: 2026-10-02
ROOT: launch-frame deferred-UI blindness (plain run = Looper t≈0 face)
SOURCE: AOSP MessageQueue/Looper nativePollOnce(timeout) law + F-NEW-197/F-115b
LAW: future-due work fires legally in real time; the launch frame predates it;
     a verdict on such a frame is PROVISIONAL and must be labeled
BEFORE: fishrings b5a7a35d5fe0564b flat #303030 with census silent (splash
        Timer 5000ms never observed); sudoku white with G08-LAUNCH after capture
CHANGE: census fields deferred_ui_pending/queue_size/earliest_ready_ms recorded
        at pump quiescence AND at capture (pending-intent snapshot); message
        annotation; launch-frame law NOT changed (frozen goldens preserved)
AFTER: fishrings --frames 14 --frame-delay 500 = a341e3ad9092f640 ×3 REAL GAME
       BOARD (6673 colors); sudoku = 45962e018344e94d ×3 (real layout + 2
       buttons; text missing = registered finding)
APK: fishrings_v1.23_vc6.apk / sudoku_secuso_101.apk
PACKAGE: eu.veldsoft.fish.rings / org.secuso.privacyfriendlysudoku
APK SHA: 14d7dd80f7563c6a / 1aff917f4ac9952b
RUN CONFIG: run <apk> --frames 14|20 --frame-delay 500 -o <out>
RUNTIME RESULT: NEW SUCCESS fishrings (previously failing -> real game content
        ×3 deterministic); sudoku PARTIAL advance (white -> real layout)
VIEWTREE/PROVENANCE: lifecycle traces + G08-LAUNCH records in run logs
SCREENSHOT: run/w2_final/fishrings_t1/screenshot.png (+frames/ sequence)
SCREENSHOT SHA: a341e3ad9092f640 (fishrings) / 45962e018344e94d (sudoku)
3-RUN: ×3 byte-identical both
NEW SUCCESS: fishrings +1
REGRESSION: none (dooz/microtimer/unote/opencalc goldens byte-identical)
COMMIT: (this wave)
ISSUE: #354
STATUS: IMPLEMENTED+TESTED
```

```text
ID: F-NEW-233
DATE: 2026-10-02
ROOT: frame-truth census was trace-gated — plain runs reported SUCCESS for
      blank frames
SOURCE: 21-P0-6 pixel-ownership law; CONSTITUTION V2 §17 (silent wrong worse
        than crash)
LAW: the honest verdict is the product of the CAPTURE, not of the trace flag
BEFORE: sudoku plain run rc=0 'Status: SUCCESS' on a 100%-white frame (verdict
        block skipped without --trace)
CHANGE: census/verdict/downgrade computed unconditionally; verdict+
        first_missing_stage persisted; annotation appended post-final-status
AFTER: sudoku plain = PARTIAL + '[F-NEW-233 frame truth: verdict=NO_ROOT,
       first_missing_stage=WINDOW_ROOT]' + deferred-UI note in the message
APK: sudoku_secuso_101.apk (live repro) + full regression battery
PACKAGE: org.secuso.privacyfriendlysudoku
APK SHA: 1aff917f4ac9952b
RUN CONFIG: run <apk> (plain, no flags)
RUNTIME RESULT: status honest; goldens unchanged
VIEWTREE/PROVENANCE: census in run message + trace
SCREENSHOT: unchanged pixels (31ddd4d5b8e6d18e)
SCREENSHOT SHA: 31ddd4d5b8e6d18e
3-RUN: goldens ×3 byte-identical after the change
NEW SUCCESS: 0 (evidence-integrity fix)
REGRESSION: none
COMMIT: (this wave)
ISSUE: #354
STATUS: IMPLEMENTED+TESTED
```

### TELEGRAM (§6 — honest state at HEAD 2026-10-02)

- telegram_official.apk: launches (rc=0 pipeline, PARTIAL by F-016 ×4
  uncaught), final face = REAL Telegram settings activity
  ("LowPowerEnabledTitle" + "Disable") — real app content but WRONG screen
  (auth/intro flow not reached) and DOUBLED title text (overlap bug).
- forkgram_709208.apk: same face (same sha bbb6cd10a834963d), REAL_APP_CONTENT
  verdict, F-016 ×6 uncaught; drifted from V10 bank cf4c41e62ceb6557
  (F-NEW-226/227 text laws changed text pixels globally — re-bank pending).
- Verdict: REAL_APP_CONTENT not demonstrated on the Telegram MAIN UI; the
  first missing laws = the intro/auth navigation chain + the title-overlap
  layout bug. NOT marked tested/success. Grey/custom-view shell ≠ success.

### §6 Telegram

| # | Item | Status |
|---|------|--------|
| 1 | telegram_official install/inspect/launch/trace/screenshot at HEAD | [✓✓] executed (PARTIAL, F-016 ×4) — real settings face, NOT main UI |
| 2 | forkgram gate re-run at HEAD | [✓✓] bbb6cd10a834963d (drifted from V10; REAL_APP_CONTENT verdict; F-016 ×6) |
| 3 | blank/grey/custom-view state identified with first missing law | [✓✓] intro/auth navigation chain + title-overlap layout bug |

### §7 Sentinels

- **Safir**: [X] BLOCKED-BY-IDENTITY — zero matches for "Safir" in registry/worklog/
  docs/evidence/issue checkpoints (searched 2026-10-02). The name does not exist in
  any project record. APK needed from user to become a sentinel. NOT silently closed.
- **Black**: same result — zero matches. BLOCKED-BY-IDENTITY.
- Working sentinels kept visible every wave: dooz d602648e8e401895, microtimer
  da73010a37dd0189, unote 4f1a9e4e8f64fae8, opencalc e364b001ee7abd66,
  forkgram cf4c41e62ceb6557.

### §9 F-NEW-230 golden validity

| Golden | Validity | Action |
|--------|----------|--------|
| whatsapp 31ddd4d5b8e6d18e | INVALID (100% white) | REJECTED as gate (2026-10-02) |
| ssw / headingcalc / secuso | STALE (not reproducible at HEAD, F-NEW-228 session) | re-bank pending |
| forkgram cf4c41e62ceb6557 | STALE-DRIFT (now bbb6cd10a834963d, still REAL_APP_CONTENT; F-NEW-226/227 text laws changed text pixels) | re-bank pending |
| dooz d602648e8e401895 / microtimer da73010a37dd0189 / unote 4f1a9e4e8f64fae8 / opencalc e364b001ee7abd66 | VALID ×3 with recorded repro blocks (2026-10-02) | banked in registry F-NEW-230 |

### §10 F-NEW-229 CL MATCH_PARENT spec law

| # | Item | Status |
|---|------|--------|
| 1 | Trace ConstraintLayout→spec→child→final width | [ ] |
| 2 | Generic fix (AOSP MeasureSpec law) | [ ] |
| 3 | Fan-out search | [ ] |

### §20–22 README / achievements / release reconciliation

| # | Item | Status |
|---|------|--------|
| 1 | README matches measured reality (no "525 roots" as headline) | [ ] |
| 2 | ACHIEVEMENTS reclassified (VALID/STALE/UNVERIFIED/SUPERSEDED) | [ ] |
| 3 | Release audit: clean git state, no stray commits, registry consistent | [ ] |

## ENTRY FORMAT (§16 — every completed item)

```text
ID: / DATE: / ROOT: / SOURCE: / LAW: / BEFORE: / CHANGE: / AFTER:
APK: / PACKAGE: / APK SHA: / RUN CONFIG: / RUNTIME RESULT:
VIEWTREE/PROVENANCE: / SCREENSHOT: / SCREENSHOT SHA: / 3-RUN:
NEW SUCCESS: / REGRESSION: / COMMIT: / ISSUE: / STATUS:
```
