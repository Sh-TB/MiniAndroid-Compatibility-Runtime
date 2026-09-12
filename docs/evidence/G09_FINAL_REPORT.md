# G09 FINAL REPORT — REAL APK CORPUS VALIDATION + G06–G08 CROSS-APP PROOF

Recorded 2026-09-06 at campaign HEAD 98c25ba2 (post FIND-G09-LC-001 fix).
Vocabulary: RESEARCHED / IMPLEMENTED / TESTED / REAL-APK TESTED /
RUNTIME-PROVEN / VISUALLY-PROVEN / VERIFIED (Rule 0.1). A fixture PASS is
never promoted to REAL-APK VERIFIED anywhere in this report.

## 0. Campaign thesis and the four proof tiers

The G09 instruction demanded the distinction between:

1. ENGINE/LAW PROOF — law batteries + project fixtures (48-gate battery).
2. FIXTURE PROOF — real-toolchain APKs built from in-repo sources
   (g06_interaction / g07_lifecycle / g08_navigation / tictactoe_golden /
   density-matrix). Provenance = in-repo sources + build logs.
3. REAL EXTERNAL APK PROOF — third-party APKs fetched from frozen public
   URLs, hash-verified, never modified.
4. CROSS-APK GENERALITY — the same law reproducing across structurally
   different applications.

G09 adds tiers 3 and 4. The battery's "tictactoe_golden" is TIER 2 (fixture
built by ECJ+D8 from in-repo sources); the F-Droid
`com.emmanuelmess.tictactoe_3` is TIER 3 — and G09 proved the two behave
DIFFERENTLY (the real one renders blank: it is a libGDX/GL game). This is
exactly the fixture-vs-real gap the campaign was launched to expose.

## A. Baseline (Phase 0)

```text
Session-start HEAD: af99f763 (main, clean; 1 unpushed commit — runtime/data
  shared-prefs residue; engine untouched)
Battery at baseline: 48 stage gates ALL PASS (scripts/test/run_test_battery.sh, now with
  same-HEAD resume checkpoints; foreground execution — the sandbox reaps
  background process groups between tool calls)
Frozen hashes reproduced BYTE-IDENTICALLY at baseline and again at 98c25ba2:
  EXT-01/EXT-02 frame_000 png  142238fd92b69e11…
  EXT-02 frame_001 png         e242ac1e9c8cc224…
  density-matrix               351340a7a92e645c  (det2/det3 identical)
  (note: frames-manifest `sha256` is an internal raw-frame hash; the frozen
   constants are the PNG file-byte hashes = png_sha256 — verified sha256sum
   against the frozen values)
Engine NOT modified before the baseline was recorded (first two commits of
this campaign are evidence/tooling + the corpus-derived lifecycle fix).
```

## B. The frozen corpus (Phase 1) — 18 real APKs

Registry: `docs/evidence/g09_corpus/g09_corpus_registry.json` (committed;
APK binaries stay OUT of git — cache under `miniandroid/download/`,
gitignored). Per-APK metadata: package, versionCode/Name, minSdk, targetSdk,
label, launchable activity, full activity list with intent-filters,
DEX census (AppCompat/Compose/support-v7, listener/result API surface),
SHA-256, source URL, frozen date.

| # | APK (package @ versionCode) | SHA-256 (16) | minSdk | targetSdk | Acts | AppCompat | Compose |
|---|---|---|---|---|---|---|---|
| 1 | com.appliberated.helloworldselfaware @ 2 | 009b467109c4d48d | 9 | 35 | 1 | no | no |
| 2 | com.emmanuelmess.tictactoe @ 3 | 760fe5acf7b39435 | 14 | 29 | 1 | no | no (libGDX) |
| 3 | de.duenndns.gmdice @ 8 | 1621eda11b5dbc0c | 11 | 27 | 1 | no | no |
| 4 | omegacentauri.mobi.simplestopwatch @ 26 | b3ec1a5ec24ce53b | 4 | 29 | 4 | no | no |
| 5 | com.chessclock.android @ 29 | 5ca6f2c54c05efe7 | 21 | 25 | 2 | no | no |
| 6 | org.billthefarmer.notes @ 139 | 82cf8bc44c163748 | 21 | 28 | 4 | no | no |
| 7 | org.debian.eugen.headingcalculator @ 1 | 274ec873098eea51 | 5 | 19 | 1 | no | no |
| 8 | com.benny.openlauncher @ 39 | b3320463a7a1ed46* | 17 | 28 | 9 | YES | no |
| 9 | io.github.yamin8000.dooz @ 18 | d81292cd346dcb23 | 24 | 34 | 1 | no | YES |
| 10 | nl.hansdezwart.bgclock @ 2 | 72c140b0083ef273 | 26 | 36 | 1 | no | no (WebView) |
| 11 | com.github.muellerma.stopwatch @ 6 | 3b6a10c8dc8ddc72 | 24 | 33 | 0† | YES | no |
| 12 | rkr.simplekeyboard.inputmethod @ 145 | d83060833dc2bc97 | 24 | 36 | 1 | no | no |
| 13 | dubrowgn.microtimer @ 8 | 79c6f730f64886e7 | 28 | 34 | 1 | no | no |
| 14 | app.varlorg.unote @ 30 | be91103f0e7db443 | 21 | 34 | 9 | no | no |
| 15 | fr.neamar.kiss @ 224 | da6ab0b1219ad3b5 | 21 | 36 | 5 | YES | no |
| 16 | org.fossify.notes @ 13 | 5a56e0e39cc488e1 | 26 | 36 | 31 | YES | YES |
| 17 | net.gsantner.markor @ 163 | 3f9f260dc3e32a12 | 18 | 35 | 12 | YES | no |
| 18 | org.connectbot @ 11009000 | 191e6990a4db95b0 | 24 | 36 | 1‡ | YES | YES |

\* CORPUS DRIFT: F-Droid today serves `b3320463…` for openlauncher_39; the
prior manifest froze `b7900f56ccbe4768…` (upstream re-sign/republish). G09
freezes today's bytes and records both hashes.
† manifest declares 0 `<activity>` elements reachable by our parser at this
version (registry records this anomaly).
‡ ConnectBot 11009000 declares exactly ONE Activity + 3 Services (single-
Activity Compose-era architecture). This CORRECTS the prior G06–G08 record
that called EXT-08 a "real multi-Activity app" — manifest evidence over
assumption.

Not frozen (recorded, with reasons):
- org.telegram.messenger — `https://telegram.org/dl/android` is not a frozen
  APK URL (redirect page); registry-only.
- com.martinmimigames.tinymusicplayer_1 — F-Droid URL returns **404**
  (package removed upstream). Dead frozen URL recorded.

## C. Required result table (Phases 2/3/4/5 + earliest blocker)

Per-APK chain: REAL APK → real DEX → real View tree → canonical input
dispatcher → state mutation → callback → frame update → visible result.
Statuses: PASS / PARTIAL / FAIL / N/A (app or capability genuinely absent).

| APK | SHA-256 (8) | Initial UI | G06 Input | G07 Lifecycle | G08 Navigation | API 9 | API 10 | Earliest blocker |
|---|---|---|---|---|---|---|---|---|
| helloworldselfaware | 009b4671 | RENDERED (golden) | PASS (long-press 12/12, VISUALLY-PROVEN) | PASS (RESUMED chain) | N/A (1 act) | N/A | N/A | — |
| tictactoe (F-Droid) | 760fe5ac | BLANK | N/A (GL game, no View listeners) | PASS (boot chain) | N/A | N/A | N/A | **F12** libGDX/GLSurfaceView |
| gmdice | 1621eda1 | RENDERED (rich) | PASS 8/8 probed, 8 state-changed (VISUALLY-PROVEN) | PASS | N/A (1 act) | N/A | N/A | — |
| simplestopwatch | b3ec1a5e | RENDERED | PASS 4 probed, 2 visual (real DEX onButtonStart/Reset/Settings/Menu) | PASS | PARTIAL (menu buttons dispatch handlers; no second Activity in probed flows) | N/A | N/A | — |
| chessclock | 5ca6f2c5 | PARTIAL ("null" texts) | PARTIAL (8 probed, 0 visual; data layer null) | PASS | BLOCKED: implicit intent → `G08-LAUNCH FAILED: no component` | N/A | N/A | **F10** implicit Intent |
| billthefarmer notes | 82cf8bc4 | PARTIAL (2 rows collapsed top-left) | PARTIAL (2 dispatched, 0 visual) | PASS | N/A (getIntent only) | N/A | N/A | **F8** list-item measure |
| headingcalculator | 274ec873 | BLANK (custom views: 1080x0 + no draw) | FAIL (nothing probeable) | PASS | N/A | N/A | N/A | **F8/F9** custom-View measure/draw |
| openlauncher | b3320463 | BLANK shell (f0f0f0) | N/A (no views) | PASS (RESUMED) | N/A | N/A | N/A | **F12** AppCompat shell |
| dooz | d81292cd | BLANK | N/A | PASS | N/A | N/A | N/A | **F12** Compose |
| bgclock | 72c140b0 | BLANK (dark) | N/A | PASS | N/A | N/A | N/A | **F12** WebView (androidx.webkit) |
| muellerma stopwatch | 3b6a10c8 | PARTIAL (bar only) | N/A | FAIL (boot dies pre-onCreate) | N/A | N/A | N/A | **F5** `NoClassDefFoundError` in AppComponentFactory chain (FIND-G09-ACF-001) |
| simplekeyboard | d8306083 | BLANK | N/A | PASS (RESUMED) | N/A | N/A | N/A | **F5** Preference/Fragment settings surface |
| microtimer | 79c6f730 | PARTIAL (keypad collapsed to left column) | PARTIAL (12 probed, 0 visual) | PASS | N/A | N/A | N/A | **F8** row/item width measure |
| unote | be91103f | RENDERED (checkboxes, FAB, toolbar) | PASS 4 probed, 2 visual | PASS (full chain + lawful cascade) | BLOCKED at addNote: Intent without component → ACTIVITY_NOT_FOUND | N/A | N/A | **F10** component-less Intent (FIND-G09-INT-001) |
| KISS | da6ab0b1 | BLANK shell | N/A | PASS (full CREATED→STARTED→RESUMED) | N/A | N/A | N/A | **F12** AppCompat shell |
| fossify notes | 5a56e0e3 | BLANK | N/A | PASS | N/A | N/A | N/A | **F12** Compose (+AppCompat) |
| markor | 3f9f260d | BLANK shell | N/A | PASS | N/A | N/A | N/A | **F12** AppCompat shell |
| connectbot | 191e6990 | BLANK | N/A | PASS | N/A (single-Activity app — corrected) | N/A | N/A | **F12** AppCompat/Compose shell |

### Totals (12 required statistics)

1. **Total APKs tested**: 18 (all REAL-APK TESTED at HEAD 98c25ba2; base +
   click-test runs; console logs + JSON evidence per APK committed).
2. **Real-APK passes (initial UI RENDERED)**: 4 — helloworldselfaware,
   gmdice, simplestopwatch, unote.
3. **Partials**: 5 — chessclock (null data), billthefarmer (collapsed rows),
   microtimer (collapsed keypad), muellerma (partial bar + boot fail),
   headingcalculator counted below as blank (custom views) — so 4 partials
   with visible-but-wrong content.
4. **Failures (blank window)**: 10 — tictactoe, openlauncher, dooz, bgclock,
   simplekeyboard, KISS, fossify, markor, connectbot, headingcalculator.
5. **N/A**: G06 input on 10 apps (no probeable View surface or GL/Compose);
   G08 navigation on 16 apps (no multi-Activity flow reachable in probed
   paths).
6. **Cross-APK findings**: see §D clusters.
7. **Fixes implemented this campaign**: 1 generic law (FIND-G09-LC-001,
   commit 84f0fb55) + corpus-derived law tests (22→25 checks). Verified on 6
   structurally different APKs; full 48-gate regression green.
8. **Regression result**: BATTERY GATE ALL PASS (48/48) at 98c25ba2, all
   frozen goldens byte-identical (§A).
9. **Golden results**: G01 typography 9/9; G02 interaction 12/12; density
   oracle 11/11; G06 21/21 + 3-run; G07 16/16 + 3-run; G08 17/17 + 3-run;
   helloworld 26; tictactoe-fixture 8; lifecycle law 25/25; input law 45/45.
10. **API 9/10 findings**: see §E — API-level 9/10 is NOT a modeled axis in
    MiniAndroid; the only version-sensitive law is resource v-qualifier
    selection (already law-tested 48/48). API 9/10 matrix = NOT APPLICABLE
    as a runtime switch (documented, code-anchored).
11. **Highest-impact remaining blockers**: F12 AppCompat shell (6 apps),
    F12 Compose (3 apps), F8 measure laws (3 apps), F10 implicit/component
    Intents (2 apps), F5 AppComponentFactory (1 app + cluster risk), F12
    WebView (1 app), F12 GL (1 app).
12. **Recommended next campaign**: ranked in §F — winner: **ListView/
    TableRow child-measure law (F8 cluster)**, runner-up: AppCompat shell
    (F12, 6 apps) with AppComponentFactory as its entry law.

## D. Phase 6/7 — failure clusters → generic law fix

### CLUSTER-L2 (FIXED): lifecycle record advancement

- Evidence: BEFORE the fix, 10+ framework-only APKs recorded
  `ACTIVITY_CREATED→RESUMED` directly (skipping STARTED) and 4+ apps
  recorded REJECTED (success=false) finish cascades
  (`ACTIVITY_CREATED→PAUSED→STOPPED→DESTROYED` all guard-rejected, e.g.
  unote). Two structurally different populations: apps that override
  onStart/onResume with real code (KISS — full chain) vs apps where the
  framework stub answers (unote, simplestopwatch, chessclock, microtimer,
  bgclock, markor, connectbot…). Reproduced on ≥2 structurally different
  APKs ✓.
- Root cause (commit 84f0fb55): the boot driver gated the machine's STARTED
  and RESUMED transitions on app-visible DEX dispatch success. AOSP law
  (ActivityThread.handleLaunchActivity → handleStartActivity →
  handleResumeActivity): the activity record advances on the FRAMEWORK path
  whether or not the app overrides the callback.
- Fix: unconditional record advancement at boot; the trace still records
  whether real app bytecode ran. Focused law test added (lifecycle_law_test
  22→25): CREATED→RESUMED without STARTED stays REJECTED; the lawful
  stub-answered boot chain terminates RESUMED and the FULL finish cascade is
  legal from it.
- Verification: lifecycle_law_test 25/25; corpus re-run — unote trace now
  PROCESS_CREATED→ACTIVITY_CREATED→STARTED→RESUMED all success=true,
  final_state=RESUMED (was ACTIVITY_CREATED with 4 rejected entries); 6/6
  rerun apps RESUMED; 48-gate battery ALL PASS; frozen goldens unchanged.

### CLUSTER-L1 (classified, deferred): AppCompat/Compose/WebView/GL shells — F12

8 blank windows share the AppCompatDelegate/AppCompat widgets shell boundary
(openlauncher, muellerma, KISS, markor, connectbot, fossify) or Compose
(dooz, fossify, connectbot-partial), 1 WebView (bgclock), 1 GL (tictactoe).
Known boundary since G04+G05, now QUANTIFIED on real corpus: 11/18 apps.
No engine change (Phase 9 decision, §F).

### CLUSTER-L3 (classified): item/child width collapse — F8

microtimer (keypad column collapsed, 12 buttons probed, 0 visual change) +
billthefarmer (ListView rows collapsed into a top-left 100×100 region).
Two structurally different APKs, same visual signature: children measured
with ~zero width. Reproduced on ≥2 APKs ✓. Law identification done at the
symptom level; exact MeasureSpec spec source requires a focused session
(layout dumps committed). NOT patched in G09 (Phase 9 ranking: highest
impact × confidence — recommended NEXT).

### CLUSTER-L4 (classified): component-less Intents — F10

chessclock: real DEX `startActivity` with an implicit (settings) Intent →
`G08-LAUNCH FAILED: no component (implicit intent)`. unote: real DEX
`startActivity` from addNote → Intent has no component → ACTIVITY_NOT_FOUND.
Real-corpus answer to "does the corpus require implicit intents and how
often": **2/18 apps hit component-less dispatch in probed flows** — the
boundary is real but lower-impact than F8/F12. Deferred per Phase 4
instruction.

### FIND-G09-ACF-001 (classified): AppComponentFactory boot path — F5

muellerma stopwatch dies pre-onCreate: `NoClassDefFoundError` propagating out
of `android.app.AppComponentFactory` chain resolution (6/18 corpus apps
declare `android:appComponentFactory` — the whole AppCompat population).
Providing the API-28+ framework shell class is the generic law; bundled into
the AppCompat campaign (§F rank 2).

### Trace-semantics findings (recorded, low severity)

- onCreate dispatch records appear multiple times per boot (8 log records
  for one NoteMain creation) — dispatch-probe verbosity vs creation
  multiplicity needs disambiguation in the trace exporter.
- frames-manifest `sha256` (internal) ≠ PNG file hash (`png_sha256`) — the
  frozen constants are the PNG hashes; documented to prevent future false
  alarms (one occurred in this campaign and was resolved).

## E. Phase 5 — what "API level compatibility" means for MiniAndroid (audit)

Code-anchored findings (no blind "Android 9/10 compatible" label):

| Surface | Anchor | Modeled? |
|---|---|---|
| Resource version qualifiers (vN) | `res_config.cpp:158` (reject `sdkVersion > settings`), `:346` (AOSP closest-bucket tie-break), `:435` `c.sdkVersion = 34 // runtime target API level` | YES — device constant 34 |
| `Build.VERSION.SDK_INT` visible to DEX | `dalvik_engine.cpp:11539` `seed(…SDK_INT…, make_int(34))` | YES — constant 34 |
| Manifest minSdk/targetSdk | `manifest_reader.cpp:470-472` parsed; reported by `analyze` | METADATA ONLY |
| `ApplicationInfo.targetSdkVersion` | `android_context.h:320` default 30; no reads found | DEAD FIELD |
| Version-gated framework behavior (Theme.Material vs Holo, permission model, ActivityOptions…) | — | NOT MODELED |

**Conclusion.** MiniAndroid models a SINGLE device profile whose framework
laws are ported from AOSP 14 (SDK_INT=34) plus the resource
version-qualifier selection law. "Android 9/10 compatible" is not a claim
the architecture can express: there is no switch that changes SDK_INT,
device sdkVersion, or API-dispatch behavior per run. An APK×API9×API10
matrix would therefore produce two IDENTICAL columns (same engine), which
would be fake version evidence — refused. What IS version-sensitive and
REAL today: each corpus APK's declared minSdk (4…28) and the v-qualifier
buckets it ships (`vN` selection exercised by resource-config law battery
48/48). API 9 and API 10 semantics become meaningful only after a modeled
API-level axis exists (SDK_INT seeding switch + qualifier device value +
per-API dispatch deltas) — recorded as FUTURE with this audit as the design
baseline. Phase 8 loop: NOT APPLICABLE under the same rationale (no second
version axis modeled ⇒ no cross-version regression can exist).

## F. Phase 9 — IMPACT ranking for the next campaign

IMPACT = (# real APKs affected) × severity × architectural reuse ×
confidence in the Android law.

| Rank | Candidate | Apps | Severity | Reuse | Law confidence | IMPACT |
|---|---|---|---|---|---|---|
| 1 | **ListView/TableRow child-measure law (F8)** | 3+ (microtimer, billthefarmer; likely more inside multi-Activity apps) | high (UI unusable) | high (all list/grid UI) | high (AOSP ListView.onMeasure/MeasureSpec) | **TOP — recommended** |
| 2 | **AppCompat shell + AppComponentFactory entry law (F12/F5)** | 6 | high (11/18 incl. Compose blocked separately) | high | high for the entry law, medium for full shell | 2 |
| 3 | Component-less/implicit Intent resolution (F10) | 2 observed | medium | medium | high (PackageManager action/category matching) | 3 |
| 4 | Custom-View onDraw/measure dispatch (F8/F9) | 1 (headingcalculator) + unblocks others | high for affected | medium | high | 4 |
| 5 | Multi-touch, NinePatch, KEYCODE_BACK (carried boundaries) | — | — | — | — | unchanged |

Preselection refused: implicit Intent was previously listed as a boundary,
but real corpus evidence ranks it BELOW the F8 measure law and the AppCompat
shell. Real APK evidence decides.

## G. Determinism + evidence integrity

- Corpus 3-run byte-identity (default run, screenshot file bytes):
  simplestopwatch `ed1dfc8981c5ac7a…` ×3; gmdice `db0f4c4b9dca867a…` ×3.
- All G06/G07/G08 fixture goldens remain 3-run byte-identical (battery).
- Frozen EXT-01/EXT-02/density hashes byte-identical at baseline and at
  98c25ba2 (§A).
- No sleeps anywhere; the HandlerShadow virtual clock is the only time
  source.

## H. Commits (focused, per §23)

| Commit | Content |
|---|---|
| 84f0fb55 | fix(g07): FIND-G09-LC-001 framework-path lifecycle advancement + corpus-derived law checks (25) |
| 98c25ba2 | feat(g09): frozen 18-APK registry + metadata/runner/audit harness + per-APK results + pixel audit |
| (this) | docs(g09): final report + visual evidence + GitHub payloads |

## I. Evidence map (what to re-run from HEAD)

```bash
bash scripts/test/run_test_battery.sh                 # 48-gate regression
python3 MiniAndroid-Compatibility-Runtime/scripts/test/g09_corpus_metadata.py …
python3 MiniAndroid-Compatibility-Runtime/scripts/test/g09_corpus_runner.py   # base+click runs
python3 MiniAndroid-Compatibility-Runtime/scripts/test/g09_screenshot_audit.py
```
Corpus cache: `miniandroid/download/**` (gitignored; restored hash-exactly by
`scripts/test/fetch_corpus.py` from `miniandroid/tests/corpus/apks.json` + the
frozen EXT-01/ConnectBot paths recorded in the registry).
