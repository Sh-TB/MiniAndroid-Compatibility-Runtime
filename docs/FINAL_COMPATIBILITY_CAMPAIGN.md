# FINAL COMPATIBILITY CAMPAIGN — MASTER CHECKLIST

The ONE permanent master checklist (user directive §15). No competing checklist.
Created: 2026-10-02 · HEAD at creation: 286b4994 · Registry: 525 roots (529 at 2026-10-03: +F-NEW-234)

> **CURRENT-TRUTH RECONCILIATION (2026-10-03, continuation M1 + CONT-T6T7 repair):**
> root_registry.json = **535 roots** (through R-NEW-462); the canonical projection
> `canonical/root_cause_registry.json` was regenerated from it and is **== 535**
> (`scripts/cont_m1_root_projection.py`, generated 2026-10-03T05:51:09Z). The stale
> forensic-audit finding "canonical lags root_registry.json (492 vs 530)" is CLOSED.
> Reconciled rows below carry `STATUS — RESULT — EVIDENCE`; see also §17.

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
worklog.md (tail through F-NEW-228 completion wave), root_registry.json (525 roots
at the time read — CURRENT TRUTH 535, see header note + §17), evidence laws (FRAME_CAPTURE_TRUTH 12-item proof chain),
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
| 1 | F-NEW-221 R8 merged-class ctor/dispatch deep leg | [?] OBSERVED (not fixed) — root isolated by field-trace: R8 horizontal merge `LA/h;` ctor received an UNSET register (`Collections.emptyMap()` unbridged → move-result unset) yet `A/h.<init>` ran with no new-instance trace — EVIDENCE: root_registry.json F-NEW-221 (status OBSERVED, `current`: evidence captured / attack next wave) + worklog F-NEW-221 ISOLATED entry |
| 2 | F-NEW-217 kotlinx resume protocol (dame leg) | [ ] PENDING (evidence captured) — MutexImpl.unlock F084 spin (50,001 visits); CAS resolution PROVEN NOT the cause ([F-NEW-217] UNSAFE-CAS-UNRESOLVED = zero hits); suspected waiter-resume protocol across the virtual-thread park/resume model — EVIDENCE: root_registry.json F-NEW-217 (status PENDING, `current`: OBSERVED, SPIN-REGS/SPIN-HISTO/THROWABLE-STACK from droidify4/5); fix = next wave |
| 3 | F-NEW-204..207 P1 audit batch | [ ] PENDING (all four, honestly open) — P1-7 unconditional std::cerr/cout audit · P1-8 window-canonical view_tree_lifecycle_owner · P1-9 ViewRootImpl traversal cross-check · P1-10 final visual gate (no placeholder pixels/diag cells) — EVIDENCE: root_registry.json F-NEW-204/205/206/207 all status PENDING (per-item evidence fields); no fix wave has landed for any of the four as of this pass |
| 4 | F-NEW-192 | [!] REGISTERED (open residue) — elevation/translationZ not modeled in the frame walk (AOSP View.draw order otherwise enforced) — EVIDENCE: root_registry.json F-NEW-192 (status REGISTERED; scripts/fc_audit_stubs.py census; draw-walk audit execution_engine.cpp L3640-4460); worklog PHASE 10 |
| 5 | secuso grey/white-face rendering/provenance | [~] PARTIAL ADVANCE, real UI render open — org.secuso.privacyfriendly2048 canonical row: "S87: secuso tutorial screen painted (uniq 160, Skip button; was engine-default blank)", rendered=true, level NONBLANK_NEARBLANK_GATE, remaining "real UI render (near-blank engine-default shell class at HEAD)" (docs/evidence/canonical/registry.json); sudoku_secuso_101: white 31ddd4d5b8e6d18e → 45962e018344e94d ×3 (TutorialActivity + 2 buttons; text missing) via F-NEW-232/233; notes grey-face provenance still open; secuso golden eb5ebd559cad1028 STALE (F-NEW-230, re-bank pending) — EVIDENCE: canonical registry 8 secuso rows (all OBSERVED-class, none VERIFIED) |
| 6 | §28 final deliverable refresh | [ ] |
| 7 | F-NEW-228 weight-pass (claimed DONE) — re-verify reproducible | [✓✓] opencalc e364b001ee7abd66 ×3 reproduced 2026-10-02 (plain AND from installed state) |
| 8 | F-NEW-229 CL MATCH_PARENT spec law | [?] OBSERVED (root-caused, fix attempted+reverted, still open) — spec trace DONE ([U007-SPEC] view 612 spec=1080/AT_MOST; [U007-SPEC-OUT] content=579x1920): real CL fills width=1080, MiniAndroid CL-branch fallback measures 579→TableLayout 504 → opencalc rows 462 wide; attempted fix documented then REVERTED — EVIDENCE: root_registry.json F-NEW-229 (status OBSERVED; opencalc res/9t.xml SlidingUpPanelLayout lp=-1/0dp, only vertical constraints); worklog "attempted+reverted fix documented" |
| 9 | F-NEW-230 golden provenance/config gap | [~] PARTIAL — valid goldens re-banked ×3 with repro blocks (dooz d602648e8e401895 / microtimer da73010a37dd0189 / unote 4f1a9e4e8f64fae8 / opencalc e364b001ee7abd66, plain AND installed-state for opencalc); ssw/headingcalc/secuso/forkgram re-bank pending; whatsapp white golden REJECTED — EVIDENCE: root_registry.json F-NEW-230 (status PARTIAL, re-bank JSON in evidence field) + scripts/f228_regress.sh matrix (dooz/microtimer/unote MATCH@1920 ×3; ssw/headingcalc/secuso/whatsapp DRIFT patch-neutral) |
| 10 | Families A–W root/fan-out audit | [~] wave-2 established the deferred-UI fan-out family (fishrings/klondike/sudoku/chess/tripeaks/flappycow/ballbreak all pass through it) |
| 11 | Real-APK matrix refresh | [~] MEGA-W2 random ledger row 1 + regression battery banked |
| 12 | Installed-APK filesystem model proof | [✓✓] F-NEW-231 package store — 10/10 platform claims PASS |
| 13 | APK-inspection skill feasibility | [ ] |
| 14 | README/front-page audit | [✓✓] ADDRESSED — README front page now carries the capability/status section generated from canonical state (0→100 STATUS table: 150 titles = 88 games · 61 apps · 1 fixture; capability registry 197; only pixel-proven demos in the front table) — EVIDENCE: README.md §0→100 STATUS + §CONTROL SYSTEM; docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-004 (registry 148→150 titles, README/ACHIEVEMENTS totals synchronized, tools/verify_canonical_evidence.py 0 FAIL) + PIXEL-TRUTH audit row (achievements_readme_sweep: "README front table lists only pixel-proven demos"); homepage capability pass = continuation T9 |
| 15 | Version/release audit + release candidate | [~] IN PROGRESS — current truth banked: canonical registry 150 titles (docs/evidence/canonical/registry.json; verifier R1–R12 = 0 FAIL, REG-CURRENT-004); docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl = 390 rows (canonical forensic record); root projection 535 (canonical/root_cause_registry.json, continuation M1); release candidate NOT cut — working tree still carries in-flight continuation edits, so the audit stays open honestly |
| 16 | Registry/worklog/evidence reconciliation | [✓✓] RECONCILED (2026-10-03) — stale "492 vs 530" lag CLOSED: canonical/root_cause_registry.json regenerated from root_registry.json, both = 535 (continuation M1, scripts/cont_m1_root_projection.py, generated 2026-10-03T05:51:09Z); canonical registry 148→150 titles with README/ACHIEVEMENTS totals synchronized (REG-CURRENT-004); FORENSIC_ALL_REQUESTS_LEDGER.jsonl 390 rows; uninstall PENDING row closed (REG-CURRENT-003) — EVIDENCE: canonical/root_cause_registry.json `total: 535` + docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-003/004 |

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
| 10 | F-NEW-234 per-package context-root law (installed-app FILESYSTEM) | [✓✓] 3-layout mismatch root-caused + generic fix; 12 installed runs ×3 all per-package; see IAPK wave entry |
| 11 | Package data dirs consumed by runtime (was decorative) | [✓✓] 23/23 runtime-created files under data/data/<pkg> |
| 12 | Source-APK hiding test (mandatory) | [✓✓] 4 targets physically quarantined during ALL runs; runs succeeded from identity only |
| 13 | Recursive filesystem tree + state diffs (A→E) | [✓✓] manifests + diffs in run/iapk/after |
| 14 | Runtime file-IO provenance (MINIANDROID_FILE_IO) | [✓✓] telegram r1 = 100 ops, 3 honest failures; app-DEX callers recorded |
| 15 | Asset byte-source provenance (INSTALLED vs SOURCE vs APP-DATA) | [✓✓] gfx byte_source + file-IO 'assets/… @ apk=<store>/data/app/<pkg>/base.apk' |
| 16 | Telegram installed test (large app, 64MB) | [✓✓] bbb6cd10a834963d ×3 from identity; 22 data files/10.6MB; filesystem NOT the settings-face cause (intro/auth nav chain remains) |
| 17 | Large-app filesystem scaling (TARGET D + TG) | [✓✓] chess (assets+sounds) + telegram 10.6MB data tree |
| 18 | Persistence / reinstall cycle | [✓✓] prefs persist + reinstall → clean → re-created; UNINSTALL_SEMANTICS now PROVEN (was PENDING "no command" — closed by the #365 wave): uninstall removes codePath + data/data/<pkg> + external Android/data/<pkg>; reinstall = clean namespace; NOT_INSTALLED honesty rc=2 — EVIDENCE: scripts/forensic_uninstall_proof.sh ALL PASS 16/16, docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-003 (+ re-proven in the CURRENT-HEAD-TRUTH row, uninstall_proof_gate 16/16) |
| 19 | Installed-vs-sideload comparison | [✓✓] opencalc + bouncy byte-identical across both modes |
| 20 | Reusable installed-app audit capability | [✓✓] `pkgaudit --package <pkg> --data-root <dir>` (generic, JSON) |
| 21 | Uninstall command | [✓✓] IMPLEMENTED+TESTED — was "PENDING (no command exists — recorded, not faked)"; the #365 forensic wave landed `uninstall` (main.cpp cmd_uninstall + uninstall_remove_tree; removes codePath, internalData, externalData/cache trees; mirrors PMS NAME_NOT_FOUND honesty) — RESULT: scripts/forensic_uninstall_proof.sh 16/16 ALL PASS (two-package store lifecycle: install ×2 → uninstall one → probe intact → NOT_INSTALLED rc=2 → reinstall clean → store empty) — EVIDENCE: docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-003 + CURRENT-HEAD-TRUTH row (uninstall_proof_gate ALL PASS 16/16, re-run at continuation HEAD after the fix); regression gates re-run clean after the capability landed |

### §4–5 Random corpus loop

| Iteration | Seed | Random APK 1 | Before | Root | After | Random APK 2 | Before | Root | After |
|----------:|------|--------------|--------|------|-------|--------------|--------|------|-------|
| MEGA-W2 | 20261002 | sudoku_secuso_101 (app, sha 1aff917f4ac9952b) | 31ddd4d5b8e6d18e WHITE (rc=0, false-SUCCESS pre-F-NEW-233) | F-NEW-232/233 + splash-Timer deferred UI | 45962e018344e94d ×3 (TutorialActivity + 2 buttons; text missing) | fishrings_v1.23_vc6 (game, sha 14d7dd80f7563c6a) | b5a7a35d5fe0564b flat #303030 | F-NEW-232 (splash Timer 5000ms never observed) | a341e3ad9092f640 ×3 REAL GAME BOARD |
| IAPK | 20261003 | app.varlorg.unote_30 (app, sha be91103f0e7db443) | golden 4f1a9e4e8f64fae8 (sideload-verified) | — (law check: installed-mode fidelity) | 4f1a9e4e8f64fae8 rc=0 FROM INSTALLED IDENTITY (= golden; notes.db per-package) | WhatsApp_real (app, sha a013d2250a28c8f2) | 31ddd4d5b8e6d18e white (known frontier) | — (no regression; F-NEW-233 honest NO_ROOT) | 31ddd4d5b8e6d18e PARTIAL rc=1 installed-mode (same known face) |

### WAVE ENTRIES (§16 format)

```text
ID: F-NEW-234
DATE: 2026-10-03
ROOT: PER-PACKAGE CONTEXT-ROOT LAW GAP — three incompatible app-storage layouts;
      install-created data/data/<pkg> decorative; Context files/cache/db flat
      (cross-package contamination); prefs non-AOSP shape
SOURCE: AOSP ContextImpl getFilesDir/getCacheDir/getSharedPreferences/
        getDatabasePath/getDir/getExternalFilesDir laws (android-14)
LAW: every Context-anchored dir is scoped to the RUNNING package;
     MiniAndroid mapping <data-root>/data/data/<pkg> + shared volume
     <data-root>/storage/emulated/0 (documented deviation)
BEFORE: live STATE B→C diff — telegram cache4.db family written to FLAT
        <store>/files/ (shared across packages); install dirs stayed EMPTY
CHANGE: Storage::set_context_package/context_dir/package_data_dir/
        external_app_dir law family; 16 engine sites re-anchored; wired at
        set_package_info (sideload AND --package); install creates
        code_cache/no_backup; MINIANDROID_FILE_IO file-IO provenance
        instrument; gfx byte_source classification; reusable `pkgaudit`
AFTER: 12 installed runs (4 targets ×3, sources quarantined) — all 23
       runtime-created files under data/data/<pkg>; telegram 22 files/10.6MB;
       asset reads prove installed base.apk as byte source
APK: opencalculator_53 / bouncy / telegram_official / chess_jwtc_298 / unote_30 /
     WhatsApp_real (seeded randoms)
PACKAGE: com.darkempire78.opencalculator / com.dozingcatsoftware.bouncy /
         org.telegram.messenger.web / jwtc.android.chess / app.varlorg.unote /
         com.whatsapp
APK SHA: 2642613868a8a80f / ffda0d9cb0b1b2aa / e37aced2a49c1dbb / 3245b9ec35f6c1df
         / be91103f0e7db443 / a013d2250a28c8f2
RUN CONFIG: run --package <pkg> --data-root <store> (MINIANDROID_FILE_IO +
            MINIANDROID_GFX_PROVENANCE) ×3; sources physically hidden
RUNTIME RESULT: opencalc e364b001ee7abd66 ×3 rc=0 (= golden); bouncy
        b6dde6074bf47264 ×3; chess b5a7a35d5fe0564b ×3; telegram
        bbb6cd10a834963d ×3 — installed identity ONLY, byte-identical
VIEWTREE/PROVENANCE: lifecycle apk=<store>/data/app/<pkg>/base.apk; file-IO
        JSONL ops 100 (tg r1) with app-DEX callers; asset provenance
        'assets/… @ apk=<installed base.apk>'
SCREENSHOT: run/iapk/after/<target>_r{1,2,3}/screenshot.png
SCREENSHOT SHA: e364b001ee7abd66 / b6dde6074bf47264 / b5a7a35d5fe0564b /
        bbb6cd10a834963d (all ×3 identical)
3-RUN: ×3 byte-identical all four targets (+ unote random = golden ×1)
NEW SUCCESS: installed-app FILESYSTEM model proven (platform capability);
        unote first installed-mode golden reproduction
REGRESSION: none — dooz/microtimer/unote/opencalc goldens ×3 MATCH under the
        new law; whatsapp random = known face (no drift)
COMMIT: (this wave)
ISSUE: #354
STATUS: IMPLEMENTED+TESTED
```

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

Evidence for this table (2026-10-03 check): root_registry.json F-NEW-230 status PARTIAL
with the re-bank record in its evidence field ({valid_x3_with_repro: dooz/microtimer/
unote/opencalc with full repro commands}); drift matrix scripts/f228_regress.sh —
dooz/microtimer/unote MATCH@1920 ×3, ssw/headingcalc/secuso/whatsapp DRIFT equally on
HEAD baseline AND F-NEW-228 patch binaries (patch-neutral). No row of the table above
changed since the re-bank; the four stale goldens remain unre-banked (honest).

### §10 F-NEW-229 CL MATCH_PARENT spec law

| # | Item | Status |
|---|------|--------|
| 1 | Trace ConstraintLayout→spec→child→final width | [?] OBSERVED — traced live: [U007-SPEC] view 612 spec=1080/AT_MOST; [U007-SPEC-OUT] content=579x1920; chain real-CL 1080 → MiniAndroid fallback 579 → TableLayout 504 → rows 462 wide — EVIDENCE: root_registry.json F-NEW-229 evidence field (opencalc res/9t.xml SlidingUpPanelLayout lp=-1/0dp with only vertical constraints) |
| 2 | Generic fix (AOSP MeasureSpec law) | [ ] OPEN — fix attempted once and REVERTED with documentation (worklog); no generic law landed; registry F-NEW-229 remains OBSERVED, not IMPLEMENTED |
| 3 | Fan-out search | [ ] OPEN — no fan-out sweep executed for the CL MATCH_PARENT family as of this pass (honest: only opencalc res/9t.xml recorded) |

### §20–22 README / achievements / release reconciliation

| # | Item | Status |
|---|------|--------|
| 1 | README matches measured reality (no "525 roots" as headline) | [ ] |
| 2 | ACHIEVEMENTS reclassified (VALID/STALE/UNVERIFIED/SUPERSEDED) | [ ] |
| 3 | Release audit: clean git state, no stray commits, registry consistent | [ ] |

### §14 LOADING ARCHITECTURE AUDIT (2026-10-03 — installed-filesystem + full file/resource/media campaign)

Deliverables: `docs/REAL_ANDROID_LOADING_ORACLE.md` (AOSP oracle) ·
`docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md` (full diff + 38 roots in 7 families) ·
`docs/LOAD_COMPATIBILITY_MATRIX.jsonl` (36 layers). Census: 164 files/137,756 lines,
64 TUs live, 13 dead, World-A test-only, canonical path proven.

| # | Item | Status |
|---|------|--------|
| 1 | Laws read + LAWS_PRINTED | [✓✓] CONSTITUTION §16/17/25/26, CAMPAIGN_STATE, ROADMAP, FINAL_CAMPAIGN, worklog IAPK, F-NEW-231..234 registry, AOSP oracle |
| 2 | SOURCE_FILE_CENSUS (no file outside audit) | [✓✓] 164/137,756; dead+stale build metadata flagged |
| 3 | Canonical run path + split-brain verdict | [✓✓] WORLD B production; WORLD A test-only; ApplicationRuntime megabatch-only |
| 4 | REAL_ANDROID_LOADING_MATRIX | [✓✓] oracle doc, 14 law families + 12 universal questions |
| 5 | MINIANDROID_LOADING_MATRIX (36 layers) | [✓✓] jsonl + compatibility doc |
| 6 | First-divergence structural roots (not per-app) | [✓✓] 38 roots line-cited; 7 fan-out families |
| 7 | WE FORGOT THIS list (new classes) | [✓✓] 20 items (providers stage, getAbsolutePath hijack, FileOutputStream void, FD void, popen(unzip), prefs corruption, WAL, Intent.getData null, frozen config, …) |
| 8 | Runtime live proof of P0 findings | [✓✓] 3 goldens reproduced ×3 from hidden-source installed identity; ST-4 live (/dev/urandom); P-1/P-2 NOT-OBSERVED-THIS-CORPUS (probe APK needed) |
| 9 | Fix wave for P0 roots (ST-1/ST-2/R-1/R-2/S-1) | [ ] next wave — generic infrastructure only |
| 10 | Corpus random validation after fixes (202 frozen) | [ ] |

## ENTRY FORMAT (§16 — every completed item)

```text
ID: / DATE: / ROOT: / SOURCE: / LAW: / BEFORE: / CHANGE: / AFTER:
APK: / PACKAGE: / APK SHA: / RUN CONFIG: / RUNTIME RESULT:
VIEWTREE/PROVENANCE: / SCREENSHOT: / SCREENSHOT SHA: / 3-RUN:
NEW SUCCESS: / REGRESSION: / COMMIT: / ISSUE: / STATUS:
```

## 16. LOADING-CAMPAIGN IMPLEMENTATION WAVE (2026-10-03) — audit → fix → proof

Master-request checklist (AUDIT → IMPLEMENTATION → RUNTIME PROOF →
WORKING/FAILING COMPARISON → REGRESSION):

| # | Item | Status |
|---|------|--------|
| 1 | ONE canonical path law + /data/user/0 alias + host-escape closure | ✅ IMPLEMENTED+TESTED — Storage::resolve_android_path; probe host-deny/alias/urandom asserts |
| 2 | File/Context write family (ST-2) | ✅ IMPLEMENTED+TESTED — restart counter 1→2→3; store trees |
| 3 | Asset contract (R-1/R-7) | ✅ IMPLEMENTED+TESTED — FNFE-HONEST; real list() |
| 4 | FD layer (R-2): openFd/AFD/PFD/openRawResourceFd | ✅ IMPLEMENTED+TESTED (openRawResourceFd code-proven, probe caller pending) |
| 5 | decodeStream/decodeFile (R-10/ST-5) | ✅ IMPLEMENTED+TESTED — 8x8 bitmaps from probe bytes |
| 6 | Prefs atomic/escaped/commit-truth + remove/clear (ST-6) | ✅ IMPLEMENTED+TESTED |
| 7 | SQLite WAL + single databases_dir authority (ST-7) | ✅ IMPLEMENTED+TESTED |
| 8 | Provider installation stage (S-1) | ✅ IMPLEMENTED+TESTED (launch leg) |
| 9 | Intent.getData + ApplicationInfo path identity (S-5/S-7/ST-11) | ✅ IMPLEMENTED |
| 10 | Universal loading trace (FileIoTrace READ/LIST/DELETE/RENAME + provenance) | ✅ EMITTED at every new law |
| 11 | Synthetic probe covering the APIs the corpus never calls | ✅ 23/23 gate (fixtures/loading_probe) |
| 12 | Write→read→restart ×3 + real-package persistence | ✅ probe ×3 + opencalc/chess/microtimer/unote trees |
| 13 | Package isolation | ✅ probe isolation-other-pkg=false + per-package store law |
| 14 | Working-vs-failing matrix + explanations | ✅ docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl + WORKING_APP_LOADING_EXPLANATIONS.md |
| 15 | White-screen first-missing classification (loading vs non-loading) | ✅ docs/WHITE_SCREEN_LOADING_ROOTS.md |
| 16 | Regression: goldens byte-identical | ✅ opencalc/chess/dooz/microtimer/unote ×3 + telegram ×1 == goldens |

Open frontiers (honest, next campaigns): S-2 native/dlopen, S-4 content://
query/Cursor, S-11 splits, S-3/S-13 broadcasts/services, SELECTION_FROZEN
(config/density/fonts), S-10 localStorage, ST-10 sqlite/font provenance
traces, ST-12 getDir clamp deviation.

## 17. MASTER-CHECKLIST REPAIR PASS (2026-10-03 — CONT-T6T7; issue #364 T6 + #365 T7 reconciliation)

Every row touched in this pass carries `STATUS — RESULT — EVIDENCE` (no blind ticks).
Historical wording preserved where it was already accurate; corrections made in place.

| # | Item | Status |
|---|------|--------|
| 1 | Uninstall command (§3.21) + reinstall/uninstall semantics (§3.18) | [✓✓] CLOSED — RESULT: `uninstall` landed in the #365 wave (main.cpp `cmd_uninstall`; removes codePath + data/data/<pkg> + storage/emulated/0/Android/data/<pkg>; NOT_INSTALLED rc=2 honesty; reinstall = clean namespace); two-package store lifecycle proof 16/16 ALL PASS — EVIDENCE: scripts/forensic_uninstall_proof.sh; docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-003 + CURRENT-HEAD-TRUTH row (uninstall_proof_gate 16/16 re-run at continuation HEAD); regression gates re-run clean after the fix |
| 2 | Root count (stale "492 vs 530") | [✓✓] CORRECTED — RESULT: root_registry.json = 535 roots (through R-NEW-462); canonical/root_cause_registry.json regenerated from it = 535 (projection `total`/`total_roots`: 535, generated 2026-10-03T05:51:09Z) — the "492 vs 530" lag finding is closed — EVIDENCE: root_registry.json `roots` length; canonical/root_cause_registry.json; scripts/cont_m1_root_projection.py (continuation M1) |
| 3 | F-NEW-229 (§1–2.8, §10) | [?] OBSERVED, fix open — RESULT: spec trace done ([U007-SPEC]/[U007-SPEC-OUT]; real CL 1080 vs fallback 579→504→rows 462); one fix attempted+reverted (worklog); no generic law landed — EVIDENCE: root_registry.json F-NEW-229 (status OBSERVED) |
| 4 | F-NEW-230 (§1–2.9, §9) | [~] PARTIAL — RESULT: dooz/microtimer/unote/opencalc re-banked VALID ×3 with repro blocks; ssw/headingcalc/secuso/forkgram re-bank pending; whatsapp white golden rejected — EVIDENCE: root_registry.json F-NEW-230 (status PARTIAL + re-bank JSON); scripts/f228_regress.sh matrix |
| 5 | F-NEW-221 (§1–2.1) | [?] OBSERVED (not fixed) — RESULT: R8 merged-class ctor/dispatch mismatch isolated by field-trace (unset register from unbridged Collections.emptyMap()); attack = next wave — EVIDENCE: root_registry.json F-NEW-221; worklog F-NEW-221 ISOLATED |
| 6 | F-NEW-217 (§1–2.2) | [ ] PENDING (evidence captured) — RESULT: MutexImpl.unlock F084 spin; CAS proven NOT the cause (UNSAFE-CAS-UNRESOLVED zero hits); suspected waiter-resume protocol across the virtual-thread model — EVIDENCE: root_registry.json F-NEW-217 (SPIN-REGS/SPIN-HISTO/THROWABLE-STACK, droidify4/5) |
| 7 | F-NEW-204..207 (§1–2.3) | [ ] PENDING (all four honestly open) — RESULT: P1-7/P1-8/P1-9/P1-10 remain PENDING in the registry; no fix wave landed this pass — EVIDENCE: root_registry.json F-NEW-204/205/206/207 |
| 8 | F-NEW-192 (§1–2.4) | [!] REGISTERED (open residue) — RESULT: elevation/translationZ unmodeled in the frame walk — EVIDENCE: root_registry.json F-NEW-192 (status REGISTERED; scripts/fc_audit_stubs.py census; execution_engine.cpp L3640-4460) |
| 9 | SecUSo rendering/provenance (§1–2.5) | [~] PARTIAL ADVANCE, real UI render open — RESULT: org.secuso.privacyfriendly2048 canonical OBSERVED row "S87: secuso tutorial screen painted (uniq 160, Skip button; was engine-default blank)" (rendered=true, NONBLANK_NEARBLANK_GATE, remaining = real UI render); sudoku_secuso_101 white→45962e018344e94d ×3 via F-NEW-232/233 (text missing = registered finding); all 8 secuso canonical rows are OBSERVED-class, none VERIFIED; secuso golden eb5ebd559cad1028 STALE (F-NEW-230) — EVIDENCE: docs/evidence/canonical/registry.json secuso rows; root_registry.json F-NEW-232/233 |
| 10 | README/front-page audit (§1–2.14, §20–22.1) | [✓✓] ADDRESSED — RESULT: README front page carries the capability/status section generated from canonical state (150 titles 88/61/1; only pixel-proven demos in the front table); registry sync fixed 148→150 with verifier 0 FAIL — EVIDENCE: README.md §0→100 STATUS; docs/FORENSIC_REGRESSION_STATUS.jsonl REG-CURRENT-004 + PIXEL-TRUTH audit row (achievements_readme_sweep); homepage capability pass = continuation T9. Residual: README "Engine roots closed" cell still reads 421-root vs current truth 535 — sync owed in the next README pass |
| 11 | Version/release audit + release candidate (§1–2.15) | [~] IN PROGRESS — RESULT: current truth banked (canonical registry 150 titles, verifier R1–R12 0 FAIL; FORENSIC_ALL_REQUESTS_LEDGER.jsonl 390 rows; root projection 535); release candidate NOT cut (working tree carries in-flight continuation edits) — EVIDENCE: REG-CURRENT-004; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl; canonical/root_cause_registry.json |
| 12 | Registry/worklog/evidence reconciliation (§1–2.16) | [✓✓] RECONCILED — RESULT: canonical projection == root_registry == 535 (M1); registry 148→150 titles + README/ACHIEVEMENTS totals synchronized; uninstall PENDING row closed — EVIDENCE: canonical/root_cause_registry.json (generated 2026-10-03T05:51:09Z); REG-CURRENT-003/004 |
| 13 | UPSTREAM_REPLACEMENT_PLAN dispositions (issue #364, T6) | [✓✓] WRITTEN — RESULT: UPP-001..007 each carry an honest disposition from the closed vocabulary + source-url/license/semantic-law/integration-point/tests/maintenance/why — EVIDENCE: docs/UPSTREAM_REPLACEMENT_PLAN.jsonl (UPP-001 PENDING_RESEARCH; UPP-002 AVAILABLE_NOT_USED; UPP-003 AVAILABLE_NOT_USED; UPP-004 AVAILABLE_NOT_USED; UPP-005 PENDING_RESEARCH; UPP-006 AVAILABLE_NOT_USED; UPP-007 ADAPTED) |

Honesty notes for this pass:
- Nothing was ticked without a pointer; F-NEW-204..207 and F-NEW-217 remain
  honestly OPEN/PENDING, and the release candidate is NOT declared.
- Not-findable-in-this-pass items are recorded as open rather than invented:
  the "continuation T9" attribution for the README homepage capability section
  is carried per the tasking instruction; no T9 worklog entry was located in
  this pass (the underlying evidence rows REG-CURRENT-004 + PIXEL-TRUTH sweep
  were verified directly and are the load-bearing pointers).
