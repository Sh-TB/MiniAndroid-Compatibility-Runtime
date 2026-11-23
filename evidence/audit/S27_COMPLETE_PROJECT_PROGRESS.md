# S27 COMPLETE PROJECT PROGRESS — the authoritative reconciliation (2026-11-23)

Mission type: READ-ONLY audit and reconciliation. No source modified, no issue
created/closed, no new APK downloaded. Every claim below is traceable to a
path in §13. Reconciles origin/main as of **2d79dbe7** (2026-11-23T18:13Z).

## 1. Executive summary

- The S23→S27 chain is **fully linear and pushable**: all 11 wave commits
  (a86d3e03 … 2d79dbe7) are ancestors of current origin/main; HEAD equals
  origin with a clean tree. No divergence, no orphaned work remains (the
  7e96b97e squash deliberately replaced the earlier diverged audit history —
  content preserved, parentage cleaned).
- **Coin Flip is the strongest evidence of real progress**: the S27-W4 frame
  renders the app-owned coin face ("1" heads) + Flip button, pixel-verified
  THIS session (face region 84,324 non-white px, full frame 113,430 — both
  EXACTLY matching the recorded claims) and visually confirmed from the
  screenshot, with the input click dispatched (phase_b_click=1).
- Genuinely rendering app content on current main (canonical production
  flags): **flip, dice (Dicer), guess (Ugaday/Hangman), randomix (adjudicated
  progress), pz (n-Puzzle, renders then crashes on input — Iterator law
  frontier)**. Background-only: **ttt (substitute APK), minos, chess**.
  Chrome-only: **hw (helloworldtoast)**. Still failing: **notepad (NO_ROOT;
  S23 interactive runs were FAILURE), dooz (last verified S21: FAILURE,
  0 APIs called)**. Freebloks: no fresh evidence found this session →
  PENDING.
- Shared-law integration is real and tested: the S24/S25/S26 law set
  (mContentParent adoption, Iterator/Collection, axml tag, asList dual-store,
  AnimatorSet Builder, collection copy-ctor, fresh-device-per-run) is on
  main with independent law tests (s25_laws_test 4/4, s27_audit_laws_test
  7/7) and the 61-member battery; several laws also carry only app-level
  evidence (flagged per row in §5).
- The security surface is hardened and machine-verified: 36/36 external
  findings fixed, security-law test 7/7, 6,000-input ASan/UBSan fuzz clean
  (seed 0x527A27D2), 278-site memcpy sweep clean, and the new S27-A2
  StringBuilder.setLength OOM law. **The promised post-AUDIT-2 full
  production battery rerun has NOT yet happened** (PENDING — scheduled with
  the next production build).
- **The production binary is ABSENT from the current worktree** (only test
  binaries exist under build/). Binary-level claims cannot be re-verified
  until the next `make all`; all binary evidence cited here is from the
  recorded run logs. Test binaries were rebuilt this session from current
  source (provenance certain).
- Biggest shared-runtime bottleneck: **the DEX-emulation frontier** — real
  androidx bytecode paths (Iterator semantics, paging/onLayout emulations,
  compose placement) still produce poison writes or crashes on 4 of 10 apps.

## 2. Authoritative HEAD and build identity

| item | value |
|---|---|
| origin/main | `2d79dbe776f722f8b1cfbc07f6567da0dca5e164` |
| local HEAD | same SHA, branch `main`, `git status --short` = empty |
| HEAD vs origin | EQUAL (not divergent; verified by ls-remote + merge-base) |
| 11 wave SHAs | all ANCESTOR of origin/main (merge-base --is-ancestor ×11) |
| production binary | ABSENT (no `all`/monolith binary under miniandroid/build) — BLOCKED |
| test binaries present | s27_audit2_fuzz_test, s25_laws_test, s27_audit_laws_test (rebuilt this session from current source) |
| compiler | g++ (Debian 14.2.0-19) 14.2.0, -std=c++17 -Wall -Wextra -g1/-O2 profile |
| host | 2 vCPU, 3 GB RAM, 5.8 GB disk free, GNU Make 4.4.1 |
| cmake / ccache | NOT installed in the current env (tools/dl wiped; measured historically in S14/W23 with transient installs) |
| translation units | 104 src/*.cpp; 95 objects present under build/ |
| dalvik split | DALVIK_SPLIT split machinery default; 94,305-line dalvik_engine.cpp monolith kept as DALVIK_SPLIT=0 fallback (AUD-25a) |

## 3. S23–S27 chronological progress (all commits verified ancestors)

| commit | date | wave | essence |
|---|---|---|---|
| a86d3e03 | 11-21 | S23 | easy-APK campaign: 3 interactive state-changing executions (n-Puzzle/Hangman/Minesweeper ×3 runs each) + CompositionLocal provider law generalized |
| b2b7ef25 | 11-21 | S24 | easy-APK completion: AOSP mContentParent adoption law in LIVE dispatch_attached_subtree_from; shared runtime closure |
| f2823280 | 11-22 | S25 | next-blocker laws: bind-time content parent, axml tag stamp, Arrays.asList dual-store, AnimatorSet Builder, collection copy-ctor |
| c7565dbb | 11-22 | S26-A | clean-rebuild revalidation: S25 build9 exposed as an INCONSISTENT INCREMENTAL LINK; fresh clean make re-validated |
| 2603311c | 11-22 | S26-W1 | fresh-device-per-run storage law (randomix determinism ROOT-CAUSE closed) |
| 21b4ffdb | 11-22 | S27-W1 | VectorDrawable rasterization law (#633/#634): coin face bitmap pipeline |
| e41ba912 | 11-22 | S27-W2 | androidx ViewModel initializer DSL law: SavedStateHandlesVM crash eliminated |
| f70c6c29 | 11-22 | S27-W3 | content-view attachment law (#633/#634): census reaches the app tree; flip rc=1→rc=0 |
| 06b0f090 | 11-22 | S27-W4 | onLayout authority law: the R-NEW-466/R445 DEX onLayout poison rejected; coin face painted |
| 7e96b97e | 11-23 | S27-AUDIT | 36 external findings verified 36/36 and fixed; security-law test 7/7 (squash on clean parentage) |
| 2d79dbe7 | 11-23 | S27-AUDIT-2 | friend-method re-sweep: memcpy 278 clean, 6,000-input fuzz clean, NEW setLength OOM law |

## 4. APK-by-APK compatibility matrix (current main, canonical production flags)

Stages: 1 APK pinned → 2 parsed → 3 launched → 4 lifecycle → 5 app ViewTree
→ 6 app pixels → 7 input → 8 real handler → 9 visible state change →
10 persisted → 11 reopen recovered.

| APK (sha256 in evidence) | 1-4 | 5 | 6 | 7 | 8 | 9 | 10-11 | verdict label | evidence |
|---|---|---|---|---|---|---|---|---|---|
| org.ecos.logic.flip_a_coin_3 | ✔ ✔ ✔ ✔ | ✔ | ✔ 113,430 px | ✔ click | ✔ (VM law W2) | ✔ face REAL_APP_CONTENT | n/a (stateless app) | **INTEGRATED_AND_VERIFIED** | s27w4_matrix rows w4_law/w4_flip ×3; pixel check this session |
| tech.gaskell.diceroller | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | not re-run | **INTEGRATED_BUT_NOT_RUNTIME_VERIFIED (persist)** | w3_dice 0de952bf75f89409 |
| ru.zxalexis.ugaday_15 | ✔ | ✔ | ✔ | ✔ (S23 interactive) | ✔ | ✔ | S23 runs ×3 | **INTEGRATED_AND_VERIFIED** | w3_guess 87fe26766fc48d06 + S23 |
| name.livitski…puzzle.android_2 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ then CRASH | BLOCKED by Iterator law | **PARTIAL** | w3_pz 35c4e53b; placeTilesRandom NoSuchElementException |
| com.minar.randomix | ✔ | ✔ | ✔ (W4 law rejected poison) | not re-run | not re-run | ✔ pager chrome | fresh-device law | **PARTIAL (content next layer)** | w4_rnd 5fef8090d5c9c87b adjudicated |
| com.farmerbb.notepad_122 | ✔ launch only | ✘ NO_ROOT | ✘ | ✘ | ✘ | ✘ | ✘ | **BLOCKED** | w3_np 31ddd4d5; S23 interact runs FAILURE |
| com.itsfrz.tictactoe_5 (SUBSTITUTE — original emmanuelmess APK absent) | ✔ | ✘ | ✘ background only | ✘ | ✘ | ✘ | ✘ | **BLOCKED (original APK required)** | w3_ttt d55056a8928a26ff |
| de.tcrass.minos_10004 | ✔ | partial | ✘ | ✘ | ✘ | ✘ | ✘ | **PARTIAL/BLOCKED** | w3_minos b5a7a35d5fe0564b |
| dk.cocode.chess | ✔ | partial | ✘ | ✘ | ✘ | ✘ | ✘ | **PARTIAL/BLOCKED** | w3_chess d602648e8e401895 |
| com.thehellomaker.helloworldtoast | ✔ | ✘ chrome only | ✘ | ✘ | ✘ | ✘ | ✘ | **PARTIAL** | w3_hw acdd9f05dc9c7ece |
| org.blockinger.game_14 (Minesweeper) | ✔ S23 interactive ×3 | ✔ | ✔ (S23) | ✔ | ✔ | ✔ | S23 | **INTEGRATED_AND_VERIFIED (S23-era)** | evidence/s23 + s23_apk_sha256.tsv |
| io.github.yamin8000.dooz | ✔ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | **BLOCKED** (last verified S21: 0 APIs, 32 errors) | evidence/s21/ws1_dooz_r3 |
| Freebloks | — | — | — | — | — | — | — | **PENDING** (no fresh evidence found this session) | — |

A successful rc=0 is NOT counted as rendering anywhere above; the matrix uses
census/verdict fields (REAL_APP_CONTENT / DEFAULT_BACKGROUND_ONLY /
SYSTEM_CHROME_ONLY / NO_ROOT) and pixel counts.

## 5. Shared runtime laws — integration status (S24–S26 set)

| law | commit | live source | independent test | status |
|---|---|---|---|---|
| mContentParent adoption (live dispatch) | b2b7ef25 S24-W1 | dalvik_engine_invoke.cpp dispatch_attached_subtree_from | battery + app-level (flip W3 chain) | INTEGRATED_AND_VERIFIED |
| bind-time content-parent adoption | f2823280 S25-W1a | dalvik_engine_invoke.cpp | s25_laws_test | INTEGRATED_AND_VERIFIED |
| Iterator/Collection semantics | S24-W2 family (s237-w27 lineage) | dalvik interpreter bridges | battery laws; **pz crash shows the frontier** | INTEGRATED / frontier OPEN |
| DataBinding host + generated binding | S24 (b2b7ef25) | android_shadows / bridge domain | battery law | INTEGRATED_BUT_NOT_RUNTIME_VERIFIED (no DataBinding APK re-run) |
| AXML android:tag stamp | f2823280 S25 | axml_parser.cpp | s25_laws_test | INTEGRATED_AND_VERIFIED |
| Arrays.asList slot count + dual store | f2823280 S25 | dalvik bridge | s25_laws_test | INTEGRATED_AND_VERIFIED |
| AnimatorSet Builder identity | f2823280 S25 | dalvik bridge | s25_laws_test | INTEGRATED_AND_VERIFIED |
| Collection copy-constructor | f2823280 S25 | dalvik bridge | s25_laws_test | INTEGRATED_AND_VERIFIED |
| fresh-device-per-run storage reset | 2603311c S26-W1 | storage/data_root + run harness | app-level (randomix determinism root-cause) — no dedicated unit test | INTEGRATED_BUT_NOT_RUNTIME_VERIFIED as a unit law |
| --keep-app-data behavior | S26-A addendum (c7565dbb lineage) | run harness | app-level | INTEGRATED_BUT_NOT_RUNTIME_VERIFIED |
| VectorDrawable rasterization | 21b4ffdb S27-W1 | vector_inflater/BitmapStore | flip chain receipts | INTEGRATED_AND_VERIFIED |
| ViewModel initializer DSL | e41ba912 S27-W2 | try_recursive_invoke | flip chain receipts | INTEGRATED_AND_VERIFIED |
| content-view attachment | f70c6c29 S27-W3 | dalvik_bridge_domain_app_runtime.cpp (F165) + android_shadows | flip chain receipts + census | INTEGRATED_AND_VERIFIED |
| onLayout authority (takeover/relayout gate/frame reject) | 06b0f090 S27-W4 | dispatch_view_relayout + setFrame | flip chain receipts + [S27-W4-FRAME-REJECT] | INTEGRATED_AND_VERIFIED |
| StringBuilder.setLength OOM | 2d79dbe7 S27-A2 | dalvik_engine.cpp + dalvik_bridge_domain_android_core.cpp | object-compile rc=0; **no dedicated unit test yet** | INTEGRATED_BUT_NOT_RUNTIME_VERIFIED |
| CompositionLocal provider (generalized) | a86d3e03 S23 | compose bridge | battery | INTEGRATED_BUT_NOT_RUNTIME_VERIFIED (compose spared by design) |

## 6. Coin Flip full-chain verification (S27-W1→W4, current main)

| hop | source | commit | receipt | test/evidence | before → after |
|---|---|---|---|---|---|
| APK resource → VectorDrawable parse | vector_inflater/vector_decode | 21b4ffdb | [S27-W1] vector rasterized bmp_oid=792 | flip run logs | crash/blocked → rasterized |
| rasterization → BitmapStore | BitmapStore law (S27-W1) | 21b4ffdb | bmp staged | run logs | — |
| ViewModel initializer DSL → SavedStateHandlesVM | try_recursive_invoke (dalvik_engine_invoke.cpp) | e41ba912 | [S27-W2] materialized 1 initializer → factory | w2_flip_r1..r3 | F-016 process death GONE |
| setContentView → F165 subdecor assembly | dalvik_bridge_domain_app_runtime.cpp | f70c6c29 | [F023-PARENTLINK] + [S27-W3-ADOPT] root=406 under 858 | w3_flip_r1..r3 | rc=1 → rc=0 ×3 |
| census tree receives app root | S83 stray unlink + adoption law | f70c6c29 | census children=1 → 4 with geometry | w3 runs | blank → tree |
| measurement (root 0x0 starvation) | R-NEW-438 measure takeover (pre-W4) + W4 relayout gate | 06b0f090 | [DEX-MEASURE] + [S27-W4-RELAYOUT-SKIP] | w4_diag..diag4 | 0x0 → 1080x1920 from frame 2 |
| layout poison (child.layout(0,0,0,0) every frame) | dispatch_view_relayout + setFrame defense | 06b0f090 | [T58-FRAME] receipt + [S27-W4-FRAME-REJECT] | w4_law_r1 | measured_width=0 → exact F-148 rects |
| draw walk → framebuffer pixels | software_renderer FrameBuffer | 06b0f090 | app_owned_pixels=113,430; face region 84,324 | w4_flip_r1..r3 + THIS session's PIL re-count (EXACT match) + visual read of screenshot.png | 0 px → 84,324 px |
| reproducibility on current main | — | 2d79dbe7 tree | face 6808aa29ff941dae deterministic ×3, binary-independent (dev -O0 and prod -O2 agreed) | s27w4_matrix | — |
| interaction | phase_b_click=1 dispatched | 06b0f090 run | trace events 205; real handler chain (VM) executed | w4_flip_r1/report.md | **visible post-click state change NOT independently evidenced → PARTIAL** |

Verdict: the chain `APK resource → … → framebuffer pixels` is closed and
reproducible on current main; the coin face is a CORRECT coin image (heads
"1" visually confirmed); the Flip button is present at its real position;
full interaction-to-state-change evidence is the remaining gap (PARTIAL, not
a blocker claim of full functionality).

## 7. Security audit and fuzz results (S27-AUDIT + AUDIT-2)

| item | claim | verification | status |
|---|---|---|---|
| 36 external findings | verified 36/36 confirmed (1 sub-claim refuted: html title), all fixed | commit 7e96b97e message + MiniAndroid_Audit_Verification_Report_FA.docx | IMPLEMENTED/TESTED |
| security-law test | s27_audit_laws_test 7/7 (sandbox traversal DENY, prefs-name defuse, empty-key notify, hostile axml header, framebuffer clamp, user/0 alias, prefs absolute) | rebuilt and re-run THIS session from current source: 7/7 PASS | TESTED |
| battery | "54/54" in the AUDIT commit = the law-battery count of that moment; make -n identity NOW: test-core 4 + test-hostile 3 + test-law 54 = test-all 61 (the law list grew with the audit + S18/S19 families; the fuzz battery is deliberately NOT a member — sanitizer runtime stays out of the pinned groups) | make -n target dry-run counts | TESTED (identity exact) |
| fuzz | 6,000 mutated inputs × AXML/DEX/ARSC, ASan+UBSan, seed 0x527A27D2, accepted 0/965/917, ESCAPEE 0 | make test-audit2-fuzz re-run THIS session: ALL CLEAN; log recorded | TESTED |
| memcpy sweep | 278 sites classified 129 CONSTANT/107 GUARDED/16 FLAGGED/26 UNPARSED; all FLAGGED+UNPARSED manually reviewed; 0 real findings; classifier window limitation recorded | CSV + manual review notes | OBSERVED |
| setLength OOM law | growth >1 GiB → ART OutOfMemoryError via throw_deferred (receipt setlength-oom), both engine copies | engine TUs rebuilt rc=0; s25_laws 4/4 + audit laws 7/7 regression green; **no dedicated unit test yet; full battery rerun pending** | IMPLEMENTED (runtime verify PENDING) |
| post-AUDIT-2 full production battery | promised with the next production build | NOT YET RUN | PENDING |

A security-test PASS ≠ application compatibility: the fuzz/audit waves prove
hostile-input robustness of the parsers and fences, not feature parity.

## 8. Cross-coder integration map (from the 63-row ledger + branch census)

- **Merged coder lines**: s241-law-waves (S236–S240), s237-w27, s238-audit,
  s239, s240, wave9/dev-so-clean (PR #625 merged).
- **PR #626 (wave10/dalvik-accel, 15 commits) classified SUPERSEDED-IN-FULL**
  (AUD-58): every F-NEW-7xx id, 3/3 W20 P2 fixes, P0 split, dev-so profiles —
  all present in main; no rebase/cherry-pick (would resurrect duplicates).
- **MG-011 ok-fix applied on main** (AUD-55, vector_decode.cpp:942) — the
  #633 hole closed with battery 49/49 at the time.
- **RC-12 layout-geometry work UNRECOVERABLE** (branch coder-local; AUD-53);
  partially superseded by mainline c48773a0 + 7e5473be scaleType laws.
- **#634 feature-class** (animated drawable / drawable-doc loader): not on
  main (grep=0) — DOCUMENTED_ONLY.
- **#630/#631 ten layout test apps**: coder-local artifacts, apps/ empty on
  origin — BLOCKED (no substitutes allowed).
- **Real vendored libraries on the shared link line** (Makefile LIBS,
  #536 compliance): `-lsqlite3 -lssl -lcrypto -ljpeg -lwebp -lwebpdemux
  -lmpg123 -lsndfile -lz` + QuickJS compiled in-tree (Make 1×, CMake 2× with
  BUILD_TESTS=ON) + FriBidi/HarfBuzz/FreeType for text shaping (AUD-28).
  sqlite sits behind storage/sqlite_shadow.cpp (contract laws SQL-4/5/6).
- **Dormant sources**: view_renderer.cpp listed under Makefile DORMANT_SOURCES
  (S19 census) — registry rows citing it were retargeted to layout_inflater.cpp.
- Dependency graph (single chain): corpus → Manifest/Resources (arsc/axml/
  manifest/npTc) → DEX/class loading → dalvik interpreter (opcode laws) →
  framework shadows (shadow_registry single copy after BUG-7 dedupe) →
  view/layout (layout_inflater: GridLayout Bellman-Ford PRESENT; scaleType
  parity) → canvas/drawable (renderer, vector_decode MG-011, text_shaper) →
  input/state → rendered output (canonical screenshot-hash wall) →
  regression (battery + ABBA + manifest parity). Isolated/unreached: #634
  animated vector, #630/#631 apps, RC-12 remainder, litehtml/cont24 branches
  (branch-only), the 10 layout apps.

## 9. Build and test performance

Measured THIS session (2 vCPU, -O2):
- **one-TU rebuild** (arsc_parser.cpp touch → object): **4.4 s**
- **no-op make** (up-to-date test target): **0.064 s** — incremental infra healthy
- 104 source TUs / 95 objects in the current build tree.

From committed logs (do not re-run a clean build to duplicate them):
- **full build** 350.39 s baseline → **289.85 s** with W24 tiering
  (FASTPROFILE=1 W24TIERS=1 -j2; byte-identical reps 32432d05-era; AUD-12,
  INTEGRATED) — at the effective-capacity floor 288.4 s (24–25% hypervisor
  steal, AUD-14).
- **link share** 1.5 s of the 350 s build (AUD-17) — linkers like mold/lld
  were REJECTED-EXPERIMENT (no headroom to win).
- **ccache** (W23 measurement, ccache absent from current env): cold 553.42 s
  / warm 20.94 s; warm rebuild 25.40 s (AUD-16, INTEGRATED).
- **peak RSS**: 1427 MB production -j1 (W22-C), 1235 MB cmake BUILD_TESTS=ON
  -j2 491.91 s (AUD-52), 1221 MB W24 bench — no OOM at -j2 on 4 GB (AUD-10a
  REJECTED; job pools not adopted).
- **PCH / -gsplit-dwarf / ggc-min tuning / -fno-var-tracking**: all
  REJECTED-EXPERIMENT with ABBA measurements (AUD-18..21) — do not resurrect.
- Ninja vs make: parity (AUD-24) — keep make.

Which changes force what: header edits (esp. shadow_registry.h — 278.75 s
cascade cost, W24 EXP-A) and Makefile/list edits force near-full rebuilds;
single .cpp edits are ~4–30 s per TU (dalvik_engine.cpp the giant) + up to
~1.5 s link. **Stale-object / false-incremental risk is REAL, twice
demonstrated**: (1) S26-A found the S25 "build9" result as an inconsistent
incremental link and re-validated from a clean tree; (2) this session, a
sandbox recycle restored a pre-audit tree where object mtimes made partial
builds untrustworthy until a hard reset to origin. Rule: binary-level claims
require either a clean build or provenance-verified objects.

## 10. Open blockers (ordered by dependency → impact)

1. **DEX Iterator/Collection frontier** — pz placeTilesRandom
   NoSuchElementException (S24-W2 family): blocks the "renders AND survives
   interaction" bar for pz (and general collection semantics).
2. **notepad NO_ROOT** — the app tree never materializes for
   com.farmerbb.notepad (fails since S23; the S27-W3/W4 attachment/layout
   laws did not reach it): next candidate for the attachment-law family.
3. **ttt/minos/chess background-only** — census reaches chrome but not app
   content; ttt additionally BLOCKED on the original emmanuelmess APK
   (substitute never counts).
4. **randomix AppIntro content layer** — pager chrome renders; drawables/
   labels are the next layer.
5. **#634 animated drawable / drawable-doc loader** — feature-class, absent
   from main (grep=0); needs design before code.
6. **post-AUDIT-2 full battery rerun** — owed with the next production build.
7. **environment/engineering** — original ttt/Counter/RNG/OpenCalc APKs
   absent (BLOCKED, not re-producible here); CMake WEBP define divergence
   (OPEN); 3 FORTIFY __*_chk symbols (OPEN); no CI workflows (OPEN);
   #630/#631 apps + RC-12 remainder unrecoverable without coder environments.

## 11. Superseded or invalidated claims

- AUD-06 ("~52 unnecessary links + OOM") — SUPERSEDED by measurement: default
  graph = 1 executable link; 50 links only with BUILD_TESTS=ON; OOM never
  observed.
- AUD-30 (GridLayout missing) — FALSIFIED: Bellman-Ford solver present
  (layout_inflater.cpp:2899/4364).
- AUD-32 (nine-patch missing) — PARTIAL: npTc implemented
  (execution_engine.cpp:2876); npLb genuinely absent.
- AUD-25b (5,436-line function) — SUPERSEDED by the DALVIK_SPLIT machinery.
- PR #626 — SUPERSEDED-IN-FULL (content all in main).
- S25 "build9" final round — INVALIDATED as an inconsistent incremental link
  (S26-A clean rebuild addendum).
- Coin Flip face lineage b270ff04 (blank) → b492ee85799fb2cb (face not
  painted) → **6808aa29ff941dae (current)** — the first two are superseded
  evidence kept for the before/after record.
- Tracker-closure-only claims (#618/#623/#619) — tracker state is NOT runtime
  proof; runtime rows stay BLOCKED pending original APKs.

## 12. Next priorities (dependency order — NO implementation started here)

1. pz Iterator law wave (S24-W2 frontier) — unblocks the largest
   "renders+interacts" gap with an already-named root cause.
2. notepad attachment-law diagnosis (NO_ROOT) — same law family that closed
   flip; likely the next cheap win.
3. ttt/minos/chess census diagnosis (why the app subtree stays empty) +
   obtain the original ttt APK for lawful verification.
4. post-AUDIT-2 full battery + a setLength OOM unit law — closes the
   security-wave loop with a production binary rebuilt from 2d79dbe7.
5. #634 animated-vector feature-class design + the N-fixture rows (mini-ARSC
   fixture unblocks #633 testing).

## 13. Evidence index (paths; sha256 for the produced deliverables)

| path | content |
|---|---|
| miniandroid/evidence/s27/s27w4_matrix.tsv | 16-row canonical wall (APK/hashes/verdicts) |
| miniandroid/evidence/s27/w4_flip_r1/{screenshot.png,trace_summary.json,report.md} | the verified coin-face run |
| miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv | 63-row cross-coder ledger |
| miniandroid/evidence/audit/632_FINDINGS.csv | 234/234 settled registry |
| miniandroid/evidence/audit/{MASTER_AUDIT,INTEGRATION_MAP,BLOCKED_AND_PENDING}.md | reconciliation v2.5 |
| miniandroid/evidence/audit/RAW_LOGS/ | build/battery/UBSan/branch-census raw logs |
| miniandroid/evidence/s23/s23_apk_sha256.tsv | pinned APK corpus SHAs |
| miniandroid/evidence/s21/ws1_dooz_r3/report.md | last dooz verification (FAILURE) |
| evidence/s27/s27_audit2_memcpy_sweep.csv + s27_audit2_fuzz.log | AUDIT-2 artifacts |
| evidence/audit/S27_AUDIT2_SWEEP.md | AUDIT-2 wave report |
| download/S27_COMPLETE_PROJECT_PROGRESS.md + .csv | THIS report's user mirror |
| download/MiniAndroid_Audit_Verification_Report_FA.docx | the 36-finding verification report |

Deliverable SHAs recorded at write time in the CSV's meta rows and printed in
the session log; the report file itself is reproducible from the cited paths.

