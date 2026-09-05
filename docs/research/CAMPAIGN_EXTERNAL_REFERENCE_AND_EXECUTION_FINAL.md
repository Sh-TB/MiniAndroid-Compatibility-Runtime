# CAMPAIGN FINAL — EXTERNAL REFERENCE + EXECUTION (§40/§37)

Campaign: DEEP EXTERNAL REPOSITORY MINING + COMPLETE EXECUTION PUSH +
GITHUB EVIDENCE PRESERVATION
Date: 2026-09-05 · Sandbox: local git, no credentials (push blocked).

## HEAD

```text
BASE:  5810f6e  (research-campaign final: worklog — repository research & knowledge transfer)
FINAL: b763198  (worklog: execution-push campaign final session record)
BRANCH: main
TAG:    (none this campaign; repo tags carried: none in sandbox)
```

Commit chain (this campaign, in order):
1. `738ac50` feat: AOSP gravity + text-size laws (EXT-AOSP-001/002) +
   helloworld_golden permanent §28 golden
2. `c8d17f3` research: auxiliary repo studies (android-rro, Android-Dex,
   dexterpreter URL-verified, screenshot ecosystem, sim-use retry)
3. `ede3c14` docs: §31 MASTER_EXTERNAL_REFERENCE_MATRIX (66 rows) +
   §33 EXTERNAL_KNOWLEDGE_TRANSFER
4. `fe5e5ba` docs: §26 font Cases A–F consolidated status

Amendment note: `738ac50` was amended once immediately after creation
(was `0611323`) to evict 10 corpus APK files that a tool-default cache
path had placed inside the worktree — ZERO-APK policy restored
(`apk_cache/` gitignored; commit content otherwise identical). No remote
existed; history is linear and honest.

## EXTERNAL REPOSITORIES (full table in MASTER_EXTERNAL_REFERENCE_MATRIX.md)

25 reachable repositories with pinned revisions (research campaign +
this campaign's additions: android-rro a113f0a, Android-Dex c57cbc8,
dexterpreter b83d1513, Robolectric fc357fec, Paparazzi 716755fb,
Roborazzi 6abd5fc0, Shot e102d797, Dropshots 70b8cbfd).

## REPOSITORIES FULLY STUDIED

WineDroid (21 files, 20 mechanisms) · AOSP ART · AOSP frameworks/base ·
AOSP frameworks/native · dalvik · qemu(emu-master-dev) · cuttlefish ·
crosvm · AVF · waydroid · jadx · Apktool · bundletool · droidsaw ·
skydnir · DroidVM · ARSCLib · auxten/libarsc · android-rro · Android-Dex
· dexterpreter · Robolectric · Paparazzi · Roborazzi · Shot · Dropshots.

## REPOSITORIES UNAVAILABLE

- SimulaVR/sim-use — **UNAVAILABLE** (git ls-remote: repo-not-found/
  credential prompt; second consecutive session; retry recorded; no
  substitute used).

## URL_UNVERIFIED

- AndroidRecomp · ReSource · Reveree — no identity-verifiable canonical
  upstream found (history-first search per §18); NO URLs invented.

## MECHANISMS LEARNED

66 matrix rows (MASTER_EXTERNAL_REFERENCE_MATRIX.md): WineDroid 14
transferable rows · AOSP/DEX 19+ · ARSC/toolchain 9 · runner/methodology
6 · repo-level inventory 15. Highlights: LinearLayout child-gravity law,
TextView sp law, MUTF-8 cross-check, per-method link/reject graph,
ARSC SPARSE/OFFSET16 constants, Res_value NULL-empty/dynamic-reference,
screenshot triage ladders + failure-artifact methodology.

## MECHANISMS TRANSFERRED (implementation landed + validated this campaign)

- EXT-AOSP-001 LinearLayout.setGravity container-gravity law →
  commit 738ac50; helloworld_golden centered-children evidence.
- EXT-AOSP-002 TextView.setTextSize sp→px law → commit 738ac50;
  28sp→73.5px / 14sp→36.75px render-log + pixel-band evidence.
- (Methodology transfers, no code: triage ladder, failure dirs,
  UI-tree sidecar pairing — EXTERNAL_KNOWLEDGE_TRANSFER.md §2.)

## IMPLEMENTED FIXES

1. `src/dex/dalvik_engine.cpp` — class-aware setGravity dispatch +
   setTextSize intercept (both AOSP-cited).
2. `src/framework/android_shadows.h` — set_container_gravity /
   set_text_size_px setters with AOSP provenance comments.
3. `src/resources/layout_inflater.cpp` — child-gravity fallback to
   container gravity (vertical + horizontal branches).
4. `src/runtime/execution_engine.cpp` — same fallback in the legacy
   render walk (vertical + horizontal cross-axis).
5. ZERO-APK policy restore — apk_cache/ out of index + gitignored.

## TESTS (exact numbers, all at HEAD fe5e5ba tree = 738ac50 code)

- helloworld_golden validator: **18/18 PASS**, zero skipped.
- tictactoe_golden validator: **ALL PASS (8 gate groups)** — 9/9 clicks,
  10 frames, X-WINS state machine, pixel discriminators, byte-identical
  replay (board sha 0d339d84…).
- Semantic battery: 14/14 + 55/55 + 25/25 = **94/94 PASS**.
- u011 canonical matrix: gmdice c49ed25f · microtimer 92438dca ·
  simplestopwatch **BASELINE_MATCH** (97933dbc, pixel-exact law) · unote
  df92f1d9 (intended AOSP-correct change, see below) · dooz e33e6e75 ·
  tictactoe(emmanuelmess) blank 31ddd4d5 (documented pre-existing) ·
  stopwatch(muellerma) exit 1 (documented pre-existing truncated APK).

## INTENDED BEHAVIOR CHANGE (not hidden): unote

21eb0fd3 → df92f1d9 (+6480 non-white px). Cause: EXT-AOSP-001 fallback —
uNote's XML uses container `android:gravity`; children previously stayed
top-left, now follow AOSP child-gravity resolution (FAB horizontally
centered; "Ignore case"/"Search in content" labels centered in their
halves). Exit code unchanged (0). Verified visually from the matrix
screenshot. No baseline was pinned for unote in the runner; the change
is recorded here per §39 (no classifier tampering, no silent skip).

## HELLO WORLD — full §28 evidence

- Fixture: miniandroid/tests/fixtures/helloworld_golden/ (MIT), built by
  scripts/build_fixture_apk.sh (ECJ MIT + D8/r8 Apache-2.0).
- APK SHA256:  584cda5793fac73e452038ddfc7bb9ccc80984cf322e8871530ea63e16c0f3cd
- DEX SHA256:  702989378d87fb1e193d54db0a607c8f39419cc876070c6671e1f98ec5509756
- Runtime command: `miniandroid/build/miniandroid run <apk> -o <outdir>`
- Exit status: 0 (both runs)
- Screenshot: docs/evidence/helloworld_golden/screenshot.png,
  1080×1920, SHA256 93b4262188199ce03b196d4115fc389b79a3dd6654cbdca49a30c763b30a01de
- run #1 vs run #2: byte-identical (cmp-silent).
- Chain: APK → manifest → Application → Activity.onCreate → class load →
  DEX exec → View tree → setContentView(View) → measure → layout →
  fonts → Canvas → renderer → PNG. §27 satisfied with a REAL APK — no
  synthetic screen, no hardcoding.

## TIC-TAC-TOE — full §29 evidence (re-validated this campaign)

- Real fixture APK built fresh (ECJ+D8), SHA256 de3649db…
- Launch → board visible; 9 REAL clicks dispatched through DEX listeners.
- frame0 "X to move" → frame1 "O to move" → frame7 "X WINS" (anti-
  diagonal); final board 4 X + 3 O; clicks 8/9 correctly frozen
  (gameOver early-return — Android-correct).
- Pixel discriminators: buttons fill frame; every mark in its own cell
  region (>100 ink px each); cells 0/1 stay empty; frames 7/8/9
  byte-identical (frozen).
- Deterministic replay: all 10 frames byte-identical across runs
  (0d339d84…). Validation: ALL PASS, 7-check zero-skip gate.

## REAL APK SCOREBOARD (before → after this campaign)

| Milestone | Before (5810f6e) | After (fe5e5ba) |
|---|---|---|
| §27 boot/render golden (dedicated minimal fixture) | absent | **helloworld_golden 18/18** |
| Programmatic LinearLayout.setGravity | silently inert | **AOSP-correct** |
| Programmatic TextView.setTextSize | silently inert | **AOSP-correct sp→px** |
| TicTacToe interaction | ALL PASS | ALL PASS (unchanged, byte-identical) |
| unote container-gravity rendering | top-left children | **AOSP-correct centering** |
| Aux repo coverage | 19 repos | **25 repos + sim-use retry** |

## EXECUTION SCOREBOARD (§37)

| Capability | Status | Evidence |
|---|---|---|
| APK_LOAD | PASS | helloworld + tictactoe + 6 corpus APKs run exit 0 |
| MANIFEST | PASS | plain-text fixtures + binary AXML corpus manifests parsed |
| APPLICATION_BOOT | PASS | runtime pipeline phases E–H complete |
| ACTIVITY_BOOT | PASS | onCreate executed (real DEX) |
| DEX_EXECUTION | PASS | state machines, listeners, 94/94 semantic battery |
| ANDROID_API_DISPATCH | PASS | setText/setGravity/setTextSize/addView/setContentView through bridge+shadows |
| RESOURCE_RESOLUTION | PARTIAL | ARSC @string/layout/drawable proven (gmdice); res/font open |
| ARSC | PASS | gmdice full chain; SPARSE/OFFSET16 fixtures queued (hardening, not a failure) |
| LAYOUT | PASS | linear/relative/frame + weights + (now) container gravity |
| MEASURE | PASS | real measure pass; WRAP_CONTENT; text metrics |
| FONT | PARTIAL | Cases A/B/D/E VERIFIED; C open (no corpus APK carries res/font); F spec-pinned, fixture queued |
| CANVAS | PASS | Canvas shadows + custom onDraw replay (tictactoe, headingcalc) |
| RENDER | PASS | software renderer, real per-view content |
| SCREENSHOT | PASS | PNG 1080×1920 per run; evidence committed |
| INPUT | PASS | 9/9 click dispatch |
| CLICK | PASS | listener invocation + state mutation |
| MULTI_FRAME | PASS | 10-frame sequence with per-frame manifests |
| DETERMINISM | PASS | byte-identical replay (helloworld ×2, tictactoe ×2 runs of 10 frames) |
| HELLO_WORLD | **PASS** | 18/18 validator, §28 evidence record committed |
| TIC_TAC_TOE | **PASS** | ALL PASS incl. real interaction + replay |
| TELEGRAM stress | BLOCKED | pinned 10.14.5 (sha 193ad551…) no longer served; live URL returns a 1.2MB HTML payload, not an APK; recorded, no fabrication |

## GITHUB COMMENTS

None could be created: no remote credentials in this sandbox (see PUSH).
Per §0/§42 this is reported as NOT DONE — not simulated. The commit
chain below is the persistent record; the moment credentials exist,
`git push origin main` (remote already configured) plus the §36-format
comments for: EXT-AOSP-001/002 implementation + helloworld golden +
tictactoe revalidation can be posted from this history verbatim.

## COMMITS (every SHA + purpose)

- `738ac50` — EXT-AOSP-001/002 implementation + helloworld_golden fixture,
  validator, evidence + unote regression documentation
- `c8d17f3` — auxiliary repo studies (5 repositories, exact-URL law)
- `ede3c14` — §31 master matrix (66 rows) + §33 knowledge-transfer doc
- `fe5e5ba` — §26 font Cases A–F consolidation + per-stage evidence map

## PUSH STATUS

```text
PUSH BLOCKED
Remote:        https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git (configured this session)
Branch:        main
Local HEAD:    b763198
Remote HEAD:   N/A — could not authenticate
Exact error:   git push origin main →
               "fatal: could not read Username for 'https://github.com': No such device or address"
Required user action: provide push credentials (token/ssh) in the
               environment, then `git push origin main`; the chain
               5810f6e → 738ac50 → c8d17f3 → ede3c14 → fe5e5ba → 715b0ba → b763198 is
               fast-forward-ready and docs+code consistent.
```

## REMAINING GAPS (ranked)

1. **GitHub push + §34 comments** — everything is ready; only credentials
   are missing (highest leverage: makes all evidence permanently public).
2. **Q-11 font Case-F fixture** — distinct-event semantics pinned
   (FONT-002), fixture still queued.
3. **res/font (Case C) synthetic-ARSC fixture tooling** — no aapt in the
   sandbox; needs a small ARSC writer or a corpus APK carrying res/font.
4. **ARSC hardening wave** — Q-8 sparse/offset16 fixtures, Q-10
   byte-exact round-trip harness, RRO-006 Res_value edge vectors.
5. **WineDroid diagnostics transfers** — Q-12 per-method link/reject
   report, Q-13 inspect enrichment, Q-1 MUTF-8 vectors, Q-3 zero-fill
   discriminator, Q-4 payload-is-data fixture.
6. **u011 baseline extension** — pin post-change unote hash df92f1d9 as
   the new expected (with this report as justification).
7. **Telegram stress** — obtain the pinned 10.14.5 APK out-of-band or
   re-pin the registry to a fetchable version, then re-run.
8. **view_renderer.cpp dead code** — UNIFIED_007-era parallel renderer
   no longer compiles against the current ViewNode (field drift); either
   delete or re-sync it to avoid future archaeology (found and recorded
   this session during the gravity work).
