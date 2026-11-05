# CONT-16 — FRIEND FINDINGS AUDIT #2 (post-S153, user directive: one-time check)

Directive: check whether the coder friends solved problems the main runtime line
could not or had no time for. Audit-only wave (no fix attempted). Evidence basis:
every open+closed issue fetched via API at post-S153 HEAD `5484f511`
(400 issues: 307 open / 93 closed; 47 coder-tagged). Bodies read; verdicts below
grounded only in claims that carry reproducible commands + sha-pinned artifacts.

**Honest scope disclosure:** the coder tokens are Issues-only — Coder-6 states
explicitly (issue #445) their engine commits are LOCAL ("push blocked by the
Issues-only token"). So every achievement below is PROVEN-BY-DOCUMENTATION
(their run artifacts + confirm/reject recipes), NOT yet merged into origin/main.
Merging is the follow-up decision (§5).

---

## 1. SOLVED BY CODERS — beyond my frontier (verified claim shape)

| # | Achievement | Who | Why it beats my frontier |
|---|---|---|---|
| 1 | **Mindustry FIRST REAL VISUAL RENDER** through full GL pipeline (5 generic roots: VBO-rebind stale-pointer SIGSEGV, TypedView limit/position law, engine GLSL programs never reached PGL, GL-frame compositing; + wave-1 String-regex family, false ArrayStoreException ancestry fix) | Coder-6 (#445,#444,#442,#441) | Mindustry never got past loading in any of my waves; render now has DRAW PASS rows + non-uniform screenshot with accept/refute criteria |
| 2 | **GLES-constant translation + app-GLSL-as-C-shaders** (bouncy 186 GL errors → 0 across 60 frames; bouncy's own .vert/.frag extracted and translated 1:1; attrib/uniform slot tables) | Coder-3 (#443) | My GLES bridge carried wrong enum values — a real engine-layer bug I had not found; Dodge full-session 170/170 animated |
| 3 | **Termux roots** (`android.system.Os` stat family over real host syscalls; framework-ancestry fix for false ArrayStoreException — nested `SimpleEntry` extends Object law) | Coder-6 (#444,#442) | Termux was never in my proven set |
| 4 | **VLC const-class token root** (both dispatch sites resolve token from `args[1].class_desc`; Intrinsics frontier GONE) | Coder-6 (#438 via #444) | VLC never ran in my line |
| 5 | **libGDX distinct static-init root** (missing EGL10 constant → GdxRuntimeException → `Gdx.app` SGET-MISS; ≠ #388 SharedLibraryLoad family) | Coder-2 (#451) | New family member with confirm/reject one-liners |
| 6 | **Registry drift ×2 diagnosed** (Telegram pin no longer fetchable — live link serves HTML sha-mismatch; Tiny Music Player v1 gone from F-Droid) + frozen-mirror law + `registry_link_check.py` proposal | Coder-2 (#449,#458) | I had not detected either drift; ACTION ON ME (§6) |
| 7 | **Cross-sandbox determinism proof of MY anchor wall** — Coder-2 independently reproduced byte-identical frames: uNote screenshot sha256 `7481e9b4…` == my unote pin sha16 `7481e9b4`; MicroTimer `bbd350b6…` == my pin | Coder-2 (#454,#453) | Validates S151 anchor-wall pins on foreign hardware |

## 2. IN PROGRESS (honest mid-state, not solved)

- Coder-4 four-app program: Thunderbird/Tusky/Nextcloud/ConnectBot all at
  **M0 DONE → M1 in progress** (#430-#436, E3 run records, first divergences recorded).
- Coder-5: NewPipe `NP-M0 NOT STARTED`, Joplin `JP-M0 NOT STARTED` (#422,#423; JP-G0 Hermes gate undecided).
- Organic Maps: native load planned (Stage G1/G2) — still blocked (#442).
- Mindustry 1080p perf (software rasterizer vs 150 s budget) + full GLSL→C translation — declared frontier, not fixed.

## 3. NOT TOUCHED BY CODERS — still my exclusive frontiers

| Frontier | Mentions in coder issues |
|---|---|
| **AWAIT-UP GATE** (post-DOWN UP-dispatch starvation; my S152 pinned next law) | **0** |
| **NO_ROOT Compose family face `31ddd4d5` / WindowRoot** | context mentions only (#459, #395) — no fix |
| trackbook download truncation | 0 |

## 4. Decision REQUESTED from me (coder → main coder)

- **#459 IME harness decision** (Simple Keyboard v145: 0 ViewTree nodes, white frame, 0 errors — IME apps need an input-view harness). ACCEPTED IN PRINCIPLE: an IME harness law is queued behind the AWAIT-UP gate law; the harness must inflate the input view hierarchy explicitly (no IMMS) and render the candidate bar.

## 5. The merge gap (single biggest follow-up)

Coder fixes live in their local sandboxes. Options: (a) they attach
`git format-patch` bundles to issues; (b) I re-apply from their LAW+VERIFY
recipes (each fix ships a one-command verify — feasible but duplicated work).
Recommended: (a) for Coder-6 GL stack + Coder-3 GLES translation (large diffs),
(b) for small laws (const-class token, regex family, registry checker).

## 6. Actions queued on me from this audit

1. `frozen_url` + `frozen_sha256` fields in APK_REGISTRY + `scripts/registry_link_check.py` (#449/#458).
2. AWAIT-UP GATE law (unchanged pinned next; nobody else is on it).
3. IME harness decision implementation (#459).
4. Merge path decision for coder patches (§5).

Verdict: **YES — the friends solved real problems I could not or had no time for**
(Mindustry render, GLES constants, Termux/VLC roots), plus they re-proved my
anchor wall byte-exact. Engine diffs not merged yet; merging is the next decision.

## 7. S158 VERIFICATION LOOP (2026-11-04) — first confirm/reject cycle under the 40/60/20 law

| Coder item | What I actually ran | Verdict |
|---|---|---|
| **#514 W5 (Coder-4, F-C4-566/567/568, CHM compute-bypass)** | extracted the delivered 314-line `w5_only` block from comment 6616230230; `git apply --check` CLEAN on detached `eb72df8b`; full -O2 rebuild (`build_w5`, binary `254a9be71721d961`, insurance copy kept); Gate B dooz E5 -> face `11a38a5a` byte-inert; Gate C ConnectBot stderr A/B ref-vs-W5 **normalized-identical** (method: strip ASLR ptrs/RSS/ms/store-paths/ns-timestamps + thread-order sort; validated by a same-binary-twice control — raw stderr is nondeterministic even for one binary, so their stderr sha16 pins are normalized by construction); Gate E microtimer face == standing pin `bbd350b6` prefix-exact, g2048 W5 == ref byte-exact (`ec0f05ad` both — ledger pin `f43face08` uses s151 wall flags not used in this smoke) | **تایید (APPROVED) at the delta level** — merge-safe on `eb72df8b`; F-C4-566 substance (TB Koin 510 put -> 596 nodes) remains coder-attested: TB/NC/TK APKs purged in S153, and the claimed 1610-line `w5_full` stack was NOT actually delivered in the comments (only the 314-line delta is present) |
| **Coder-4 #510 W3** | (S157-B, carried) clean-apply + compile + 12/12 anchors byte-exact | تایید at merge-gate level; 4APP numbers unverifiable |
| **Coder-5 #503 COMPOSE RENDER CLUSTER** | still PENDING in their own issue — nothing to test | رد نیست؛ awaiting artifact |

New ready-made-lever verdicts this session (dooz 40% leg, "don't reinvent the wheel"):
- jemalloc 5.3.0 LD_PRELOAD (J1): face unchanged, RSS growth 1.80 vs 1.87 MB/s -> allocator-invariant live-set growth. **رد (REJECTED)**.
- O3 + LTO + march=native rebuild (no source change): face unchanged, wall == budget. **رد (REJECTED)**.
- Remaining path to a RUNNING dooz on this VM stays the S156-pinned field-slot fast path (after cache-storage hardening) + bounded heap; no ready-made component covers it.

## 8. S159 VERIFICATION LOOP (2026-11-04) — recovered field-slot overlay measured and REJECTED; new coder items not verifiable here

Provenance: the sandbox recycle auto-commit (`303ad5b1`, UUID message) swept up an uncommitted lost-session implementation of the S156-pinned field-slot fast path ("S158 W3 overlay": W1 iput reuses the memo-banked s134 key, W2 memo-banked `s134_decl_is_dex` predicate, W3 dense per-object slot overlay over the string map for iget/iget-object/iput on DEX-declared fields, map stays storage of record, dual-write invariant). Per the verification law it was treated as unverified local code and put through the full gate (343-line patch preserved at `evidence/s156_record_loop/S159_fieldslot_overlay_REJECTED.patch`; source reverted from the working tree after the verdict).

| Item | What I actually ran | Verdict |
|---|---|---|
| **Field-slot overlay (recovered W1+W2+W3, binary `fde53d47bd5b3845`)** | full -O2 build CLEAN (code was complete); dooz E5 x1 with fixed /proc monitor: face `11a38a5a` byte-identical, api_trace +24 bytes/same counts, wall 128.1s vs 127.0s control (+0.9%); **PERF-OPS A/B** (phase clock, both binaries, fresh stores): iget 1305->1773 tpc **+35.8%**, iget-object 1312->1697 **+29.4%**, sget-object +20.5%, untouched ops +4.5..15% (uniform -7.6% ops/sec background) -> the overlay made its TARGET op family ~+25pp more expensive than background; anchors x3 apps (microtimer/g2048/opencalc) both binaries: **delta-inert byte-exact**, microtimer full-pin `bbd350b6c14fbd52` | **رد (REJECTED)**: determinism-safe but performance-NEGATIVE on the exact hot path it targets; dooz unlock criteria (face move or wall -20%) failed; do NOT merge. Design (invariant, storage-of-record law) is sound and reusable — a rework must first explain the +300 ticks/op on iget (slot-fill miss rate / plan indirection / phase-clock region) before re-proposing |
| **Monitor artifact fix** | first dooz row showed rss_grow -0.005 MB/s from a VmRSS==0 teardown sample; `s158_jemalloc_ab.monitor` now skips rss==0 and the corrected long probe reads rss_grow +1.00 MB/s | fixed in `scripts/s158_jemalloc_ab.py` |
| **dooz 380s long-budget convergence probe (REF `908d5ba6`)** | E5, max-seconds 380: face STILL `11a38a5a` at wall 405.3s; RSS +1.00 MB/s (decelerating from 1.87), minflt 239/s | dooz does NOT converge at 3.5x the standard budget on this VM; not a hard memory wall (growth decelerates) — the binding constraint is record-phase throughput; pinned-VM convergence (board `851cc176` + S155 tap->placement) remains the proof the ENGINE is correct, this VM is the limiter |
| **#515 (Coder-6 Mindustry C6-GLBD wave-8)** | Mindustry 7.0 build135 APK (`64bf33842d8f5495`) absent since the S153 purge | **not verifiable here** — coder-attested |
| **#516 (Coder-3 S141 A14: ContactListener native->Java callbacks)** | recipes delivered (bouncy Battery A/B, cheap) but the code is NOT delivered: no patch/binary in the issue, and local main has neither `S141-PROBE` nor `JavaCallbackBridge`/`CallVoidMethodV` | **not verifiable here** — coder-attested; their batteries are pre-priced (~100s total) and runnable the moment the diff arrives |
| **#484 / #472 / #403** | tracker/ledger/case-file updates only, no new artifacts | nothing to test |

Budget note: this session = dooz 40% (overlay gates + long probe) + 20% coder sweep; no ready-made lever remains untested for the dooz spin on this VM — the residual paths are the bounded-heap/no-GC structural fix and cross-VM (pinned) operation.

## 9. S160 — AWAIT-UP GATE regression debt CLOSED (2026-11-04)

| Case | Result on standing binary 908d5ba6 | Status |
|---|---|---|
| **E1 dooz board tap, gate ON** | gate row fired (`scoped render window reached in Lbw0;.d`), artifact reset, **DOWN+UP both DISPATCHED+consumed**, post-tap face movement, uncaught==6 baseline | **law re-confirmed** after the S157-B surgeries (tap path + gate intact across binary generations a793f134 -> 908d5ba6) |
| **E4 diary tap (fast-path guard)** | REAL_APP_CONTENT, click dispatched, wall 4.4s, gate silent | PASS (gate arms ONLY in the pressed-render path) |
| **E3 transistor tap** | face `5436cf81605f1c2d` == S151 pin full-16, uncaught 16, gate rows 0, tap face pre==post | **byte-reproduces the S154 E3 row** (cross-binary determinism). Honesty note: the S154 commit message said "UP delivered" but its own row + this run both record up_dispatched_consumed=false — ledger = rows, not messages |

The gate law moves to VALIDATED + REGRESSION-PROVEN. Next exclusive frontier unblocked: the IME harness law (Simple Keyboard v145: explicit input-view inflation, no IMMS).

## 10. S161 — W5 MERGED INTO MAIN (verified work added to my tree per user directive) + sweep result (2026-11-04)

| Item | What I actually ran | Verdict |
|---|---|---|
| **#514 W5-only delta (Coder-4) — MERGE** | S158 تایید + this session: `git apply --check` CLEAN on main, applied (dalvik_engine.cpp + android_shadows.cpp), full -O2 build (`512517269d9634a1`), Gate B dooz face `11a38a5a` byte-inert, Gate E microtimer full-pin + g2048 delta-inert, Gate C CB stderr normalized A/B IDENTICAL (norm rule `RSS=… MB` added — gap found by the diff sample being RSS-only) | **MERGED INTO MAIN — merge-gate POSITIVE** (coder-credited: Coder-4 #514) |
| **#516 S141b (Coder-3 re-derivation + frame-112 extension)** | achievements recorded with recipes; STILL no patch/binary in the issues (their sandbox lost the tree; re-derived into THEIR worktree only); my main lacks S141-PROBE/CallVoidMethodV | **not verifiable here** — coder-attested; batteries pre-priced ~100s for the day the diff arrives |
| **#492 / #472 / #484** | dashboard/ledger/tracker refreshes, no artifacts | nothing to test |

## 11. S162 — IME HARNESS LAW (my lane) + #459 answered (2026-11-04)

| Item | What I actually ran | Verdict |
|---|---|---|
| **Coder-2 #459 (Simple Keyboard v145, IME white frame)** | re-fetched the pinned APK (sha256 match), reproduced byte-exact on W5-merged main (face `31ddd4d5b8e6d18e`, 0 EXP092-RENDER nodes), diagnosed from the manifest + run log: SettingsActivity = framework-stub dead end; LatinIME IME service NEVER launched (no service path, no InputMethodService machinery in the engine) | **their finding CONFIRMED**; root cause = runtime gap, my lane |
| **Harness decision** | law written (docs/LAW_IME_HARNESS.md): manifest-level IME detection -> no-IMMS lifecycle drive -> attach input view to render root -> [IME-HARNESS] logging (T61) -> face/success criteria; decision comment posted to #459 (6632756338) | runtime-side harness = MINE; their 1-EditText probe = phase-2 host; registry honest `HARNESS_REQUIRED` |

## 12. S163 — RUN LANE under the user directive + sweep (2026-11-04)

| Item | What I actually ran | Verdict |
|---|---|---|
| **#459 / #472 / #484 updates** | comment/body re-fetch: #459 latest = my own decision post; #472/#484 = tracker body-edits, no comments, no artifacts | **nothing to test** (no claims made → nothing owed) |
| **Coder deliverables** | none new since S162 (S141b diff + W5-full still undelivered) | sweep only |

(S163 was a RUN-lane session per the user directive — dooz, Telegram, planner apps; the coder lane had no verifiable deltas. Details in worklog S163.)

## 13. S165 — the 10-train campaign (5 dooz + 5 Telegram) + #517 W6 delivery note (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **Telegram trains T1-T5** | T1-T3 = the committed S164 rows (baseline REAL_APP_CONTENT / provider platform-skip l9/j 28→0 / app-data seed uncaught 6→0); T4 = boot-depth extraction from the committed tg_deep run (RESUMED, 24 frames, last_exception=null, 2161 app pixels — past the S163 pc=1375 blocker); T5 = fresh 4-run A/B with an RSS monitor (baseline bin vs seedskip bin+envs) | **5/5 LANDED**: exceptions 12→0 per pair, api work 9777→9773, identical 2161 app pixels, wall unchanged (same lifecycle end-point), RSS bands overlap |
| **Dooz trains D1-D5** | D1/D2 = committed S164 rows; D3 = the DRAW-WALK CHECKPOINT surgery (env-gated, 2 replay sites) + a walk-fb histogram probe; D4 = settle on the D3 binary; D5 = full anchors on the D3 binary | **5/5 LANDED as run-lanes**: checkpoint rows fired ×8 and walks DO complete+present; the smoking gun `[D3-FB-HISTO] walk-fb distinct=1 0x000000×2073600` — the black cover is the APP's Compose paint pipeline delivering black-on-black (paint colors never reach the draw ops) = the 31ddd4d5 frontier precisely identified; settle 155.9s (family holds vs 161.7s); anchors PASS (microtimer full-pin bbd350b6, g2048 f43face08, opencalc REF==NEW on identical stores) |
| **Coder-4 #517 W6** | `w6_stack.patch` (1305 lines, sha16 d92efd2d…) + `w6_laws.patch` (569 lines, sha16 65699ca9…) delivered INLINE as real diffs for the first time (F-C4-569/570/571 + checkRange IndexOutOfBounds law) | **REAL DELIVERY — verification QUEUED**: needs the W2/W3/W4 stack applied + Thunderbird APK (absent locally since S153); first coder patch-set since W5 that is actually applicable |

## 14. S166 — the 20-train campaign round 2 (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **Coder sweep** | issues re-fetch at S165 HEAD: #505/#494/#495/#492/#516 = tracker body-edits; #519/#520/#521 (Coder 7/8/9 achievement logs) = 0 inline diffs; #517 W6 (the one real patch-set) still needs the TB APK (absent since S153) | **nothing to approve/reject this round** — W6 verification stays queued per the verification law (claims without artifacts = zero value) |

(The 20 trains were MY work-lane — 10 dooz + 10 Telegram, faster-load/lighter — full table in evidence/s166_trains/S166_VERDICTS.json; summary in worklog S166.)

## 15. S167 — #517 W6 VERIFIED AND MERGED + the S166-INTEG queued delta closed (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **TB APK restored** | F-Droid `net.thunderbird.android` vc33 (v24.0, 11 MB) fetched; sha16 `473b33da5963d0a4` == the #517 body pin **byte-exact** — the coder's own fixture reproduced | fixture verified |
| **w6_laws.patch** | extracted from comment 6634643760, fence-stripped: **569 lines, sha16 `65699ca9a235e915` == claim byte-exact** | delivery verified |
| **w6_stack.patch** | parts 1+2 fence-concatenated = 1305 lines but sha16 `95303899…` != claim `d92efd2d…` (GitHub fence byte-form unreproducible); hunk-count validator found exactly ONE corruption: the seam hunk `@@ -44021,6 +44237,242` had a stray context line (blob truth: no empty line at 44023/44024 boundary → the empty line was a lost `+` from trailing-whitespace strip on paste; true header (6,243)). Repaired `53d234e1db504568` **applies CLEAN on the author's own base blob `8c622c9`** (oracle) and **3-way CLEAN on my HEAD tree** | reconstruction documented + author-faithful |
| **Gates (REF 2a5464c2 vs NEW 53fa8392640d1279)** | microtimer **full-pin `bbd350b6c14fbd52` on the W6 binary**; g2048 `f43face08` + opencalc `63020bc7` delta-inert; dooz face `11a38a5a` byte-identical + settle 156.8==156.8s + uncaught 6==6; TG pixels 2161 / api 9773 / uncaught 0 byte-identical, same-window wall 34.7→30.0s (-13.5%) | **ALL PASS — byte-inert everywhere measured** |
| **TB A/B (the W6 headline)** | same-window pairs env-off AND seed+skip fair baseline: early death 3.4-3.7s unchanged, pixels 0 both, api 11354 identical; **IllegalStateException family 16→0 ERASED** (okhttp CacheControl + K9 DecryptedFileProvider gone); Koin NDFE now the sole death frontier (65 rows vs 51; EXCEPTION ring capped at 32 both) | **headline claim (NDFE ×32 fixed) NOT REPRODUCED on my line** — measured on the coder's lineage, not mine; the real measured win on my line = the IllegalState family elimination; TB content frontier unchanged |
| **Verdict on #517** | W6 stack+laws merged into my tree (8 files, +1447/−40), full -O2 build `53fa8392` insured; ONE-SIMPLE-TEST pass (F-C4-562 ×4, F-C4-569 ×3) | **APPROVED + merged with the TB caveat recorded honestly** |
| **S166-INTEG queued delta** | full 342-line content inspection of `S166_remote_rewrite_source_delta.patch`: every hunk = removal of my S164 code or a downgrade (6-entry theme table loses the 0x01030241 NoActionBar range → dooz dark-cover dead-end returns; sc_n hardcode loses SETCOLOR diag) | **REJECTED-BY-CONTENT-INSPECTION — no build needed** (evidence/s167_w6/S167_REMOTE_DELTA_VERDICT.json) |
| **Sweep** | issues by updated_at: all timestamps pre-S166 (≤ 2026-11-04T23:48Z); #523/#516/#492 tracker edits, no inline diffs | nothing else to verify this round |

## 16. S168 — #518 W7 VERIFIED AND MERGED (SecureRandom REC-MISS root reproduced on MY line; NDFE 65→7; residual frontier cross-corroborates the coder's W8 preview) (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **w7_laws.patch** | extracted from #518 comment 6638731163, fence-stripped single-trail form: **137 lines, sha16 `ea55443a44263012` == claim byte-exact**; `git apply --check` CLEAN on HEAD 653fb0a5 (which already carries w6_stack+w6_laws per S167) | delivery verified |
| **Patch content** | law F-C4-572 (SecureRandom `<init>` + `nextBytes` real-stream, xorshift64* constant-seed = deterministic across runs, distinct per call) + F572-CONTAINS probes in the collection contains() handler | one cosmetic defect recorded: the `[F572-CONTAINS-RET] path=array` log block is DUPLICATED (zero behavior change — logging only) |
| **Build** | full -O2 one-chunk make on 653fb0a5+w7_laws → binary `f7291feaaf778c0f` (insurance copy; coder's own binary was `d5c99397` on their lineage) | built + insured |
| **TB A/B (the W7 headline)** | back-to-back pairs, env-off AND seed+skip fair baseline (REF = standing 53fa8392): **NDFE 65→7 console rows (-89%) in BOTH arms' settings**, uncaught 37→33, wall 3.5→5.4s (app advances further before dying), face `b270ff040b3601dc` byte-identical, pixels 0 both (the 31ddd4d5 Compose paint-color frontier is a separate blocker, unchanged) | **headline claim DIRECTIONALLY REPRODUCED on my line** — major kill, not absolute zero (residual 7 rows, see frontier row) |
| **Mechanism probes (NEW arm, seed+skip)** | `[F-C4-572]` ×40 (bound): distinct fills per call (b0=246/99/128…, n=16, caller `Landroidx/work/OperationKt;.random`); `[F572-CONTAINS-ENTER]` recv=5322 items o5112/4588/4540/433/208 **== the coder's own rows verbatim**; contains-RET **FALSE 103 vs TRUE 14** (the visited-guard no longer swallows); `[W6-INCL]` list obj#203 `__array_length__=5 arr[0]=o208 arr[1]=o433` **== the coder's W6-correction rows verbatim** — the includes list is NOT hollow on my line either; the W6 "hollow list" root was wrong and the deeper SecureRandom→uuid→equals→visited-guard root is right | **root chain corroborated with mechanism rows on my line** |
| **Residual frontier** | residual 7 NDFE rows are now NONFATAL (`Scope.getOrNull` catches); new death = `InstanceCreationException` unwinding `KoinModuleKt$$ExternalSyntheticLambda1.invoke` / `SingleInstanceFactory.create` (Room storage family) — **== the coder's W8-preview entry chain verbatim** | W8 preview cross-corroborated; next pinned frontier |
| **Anchors** | microtimer **full-pin `bbd350b6c14fbd52`** on the W7 binary; g2048 `f43face08` + opencalc `63020bc7` delta-inert; dooz face `11a38a5a` byte-identical + settle both TRUE + uncaught 6==6 (wall 149.3→160.8 = S156 window drift, single pair not claimed) | **ALL PASS — byte-inert everywhere measured** |
| **"All four titles dispatch onResume"** | TB verified above; NC/Tusky/ConnectBot APKs ABSENT locally (recycle) | **NOT VERIFIED this round** — honestly marked |
| **Verdict on #518** | W7 merged into my tree (2 files, +96/−1); ONE-SIMPLE-TEST pass (F-C4-572 rows fire, bounded 40) | **APPROVED + merged; caveat = residual NDFE 7 + four-title claim unverified** |
| **Sweep (rest)** | #524 (Coder-3 A16) = verification recipes carried but body-only, no inline diffs to my tree; #439/#437/#441/#438/#495/#505/#494/#472/#484/#492 = tracker/case-file edits, 0 inline diffs | nothing else to verify this round |

## 17. S169 — W8 frontier closed on MY line (my own law, no coder patch this round): SQLiteDatabase.setVersion REC-MISS was the Room storage death (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **W8-preview answered** | the coder's #518 preview asked to "trace the first query's answer (likely PRAGMA user_version / identity-hash mis-answer)" — done on MY line with a fresh store + console forensics + a DEX decode of `K9StoragePersister.openDB()` from the pinned APK | root found, different primitive than guessed |
| **Root** | `openDB`: openOrCreateDatabase (GATE A standalone) → getVersion branch → execSQL ×2 → **setVersion(N) — ZERO handlers in the shadow (grep-proven)** → post-check getVersion()==expected FAILED (0 != N) → outlined rethrow `DBUtil$$ExternalSyntheticBUOutline0.m(String)` = RuntimeException("Storage database upgrade failed!") → K9 retry storm ×5 → Koin ICE ×101 | **REAL missing primitive: SQLiteDatabase.setVersion** |
| **Law landed** | `SQLiteDatabase.setVersion(INT/LONG)` → real `PRAGMA user_version` write on the same connection (AOSP contract) + [SQLDBG] env-gated probes (entry + not_handled tail, bounded, zero behavior) — build `991d89239e69c679` insured | one-change law, probe-verified sequence matches the DEX decode verbatim |
| **TB A/B** | upgrade_failed **25→0**, ICE **101→0**, retry storm gone (opens 5→45 = storage layer ACTIVE), wall 5.4→9.4s (app runs deeper), api 11356 identical, setversion_err 0, NOT_HANDLED 0; face changed b270ff→43bfdac6 (app advances; pixels 0 both — Compose frontier unchanged); ndfe 7 / uncaught 33 unchanged | **family ERASED** |
| **Gates** | microtimer full-pin `bbd350b6`; g2048 `f43face08`; opencalc `63020bc7`; dooz face `11a38a5a` + settle TRUE×2 + uncaught 6==6 (+0.3% wall); TG pixels 2161 / face_equal / uncaught 0==0 / api 9773 identical | **ALL PASS byte-inert** |
| **New death frontier** | `MessagingController$1.run` infinite loop (F084 halt @50001 visits) — TB reaches its mail-controller loop; APP_DRAW_OPS still missing (31ddd4d5 Compose frontier) | next pinned blocker |
| **Ledger honesty fix** | the gates save() flat-update REPLACED the anchors key — S167's verdict anchors_all_inert silently covered opencalc only; S169 gates now nested-merge and carry all three anchors | retroactive correction recorded |
| **Sweep** | #439/#437/#441/#516 = case-file/tracker edits, zero inline diffs | nothing to verify this round |

## 18. S170 — coder W8 (#522) + W9 (#525) VERIFIED + MERGED: two lines converged on ONE root (setVersion); nine W9 laws' acceptance greps pass; corpus battery byte-inert (2026-11-05)

| Item | What I actually ran | Verdict |
|---|---|---|
| **Sweep hit** | #522 (W8: F-C4-573/574/575/576/577) + #525 (W9: F-C4-578…586, 1015-line patch, "TB command-queue spin DEAD") — the coder's W8+W9 delivered in the S169 gap; #525's row 1 = MY S169 pinned frontier (MessagingController$1.run F084) | two waves to verify this round |
| **CONVERGENCE (the headline)** | the coder's W8 F-C4-574 (#522) = **the SAME SQLiteDatabase.setVersion→PRAGMA user_version law I landed independently in S169** (same root: zero handlers; same site: sqlite_shadow.cpp; same AOSP contract). My S169 commit additionally carried a duplicate-insertion defect (the identical 41-line block twice = the 82 lines) | **two independent lines, one root, one fix site — the strongest corroboration class this campaign has produced** |
| **Reconciliation** | main source restored to the S168 base (S169's duplicate superseded, preserved in git history) → w8_laws + w9_laws applied → **main == coder chain byte-identical** (verified 3-file diff vs a 69c871e4 worktree); F-C4-574 canonical (its acceptance greps fire) | S167 seam-repair precedent, cleanest form |
| **sha16 verification** | w8_laws `5562609d0c3e30f3` == #525's chain claim (`5562609d0c3e30f`, 15-char truncation); w9_laws `b708b8460eac637c` == claim EXACT (no trailing newline). **The #522 comment header's own sha16 `b5f3881feeceb43a`/622 lines is STALE vs the posted content (623 lines)** — the W9 quote is the authoritative chain | claim-exact; one stale header recorded honestly |
| **APK bootstrap** | NC `com.nextcloud.client_350000290.apk` → **`c9ba2e85b13fee45` == pin byte-exact**; TK `com.keylesspalace.tusky_145.apk` → **`8154cabe67374f2e` == pin byte-exact** (F-Droid, first try); CB already local `96cf501a83e89284` ✓ | **S168's "four-title NOT VERIFIED" caveat RESOLVED — all four pins now locally verified** |
| **Anchor bootstrap repair** | `miniandroid/build/anchor_libs` was WIPED by the session recycle (gitignored): NC/TK/CB dlopen died at `liblog.so`/`libjnigraphics.so` missing → every JNI-law test would have been unrunnable. Rebuilt from the tracked recipe `scripts/cont83_build_anchors.sh` (11 anchors; liblog.so `20ac301d011e29c0` …) | the F-NEW-387 failure class, re-learned and re-recorded |
| **Build** | full -O2 one-chunk make → `4bb7c4d424923b87` (insurance `miniandroid_s170_w9_4bb7c4d424923b87.bin`; source chain = coder chain, so the binary differs from their `de8735c1bb68c9d6` by host/timestamp only) | verified on MY line |
| **TB acceptance** | REF 991d8923 → NEW 4bb7c4d4: **VME console 50→0** (the F084 command-queue spin DEAD — the coder's W8-attribution correction confirmed: PC=0x193 is K-9's own PBQ loop, not OkHttp TaskRunner); **F-C4-578 ×8 live** (park-yield at the drain boundary); F-C4-574 ×20 (bounded as designed); F-C4-582 ×1; uncaught 33→4; ndfe 7 nonfatal unchanged; face `43bfdac6023cba66` UNCHANGED | **coder's ONE-SIMPLE-TEST PASSES** (VME 0, F-C4-578 ≥1) |
| **NC acceptance** | ULE 7→0; **RegisterNatives 337 == the coder's NC claim EXACT**; F-C4-581 ×18; account-chain laws live (583×3, 584×8, 585×2, 586×2); uncaught 39→32; converter-IAE 0 (F-C4-579 active); face `33fd925fc12e7585` UNCHANGED | **greps PASS** (converter 0, gson 0, 58x ≥6) |
| **TK acceptance** | ULE 7→0; RN 288; F-C4-581 ×9 + F-C4-582 ×1; **wall 2.4→112.3s (deep execution)**; F084 wall-budget halts ×34 in R8-minified `Lck/w;.j` / `Lij/a;.h`; **my uncaught 33 == the coder's "33 errors, ALL NEW FAMILIES" census**; face `31ddd4d5b8e6d18e` UNCHANGED (Compose paint frontier holds) | Room family dead on my line too (grep 0) |
| **CB acceptance** | ULE 11→0; **RegisterNatives 345 == the coder's CB claim EXACT**; F-C4-581 ×18; uncaught 6→1; face `b5a7a35d5fe0564b` UNCHANGED | **the JNI handshake + registration reproduces verbatim** |
| **Corpus gates (the coder's explicit maintainer ask)** | microtimer **full-pin `bbd350b6c14fbd52`**; g2048 `f43face08` inert; opencalc `63020bc7` inert; dooz face `11a38a5a` byte-identical + settle TRUE×2 + uncaught 6==6; **TG pixels 2161==2161, draw_ops 11==11, frames 9==9, REAL_APP_CONTENT both** | **ALL VISUAL ANCHORS BYTE-INERT** |
| **TG honest regression row** | uncaught 0→6 (`Ll9/j;` ×2 escapes, NONFATAL, via `FirebaseInitProvider.onCreate`): on REF `libtmessages.49.so` dlopen FAILED (missing anchor) and the native-init block degraded silently; on NEW **dlopen OK + JNI_OnLoad 0x10006 + real GetMethodID registrations** (`AnimatedFileDrawableStream` …) → Telegram's real native-init path (`Lt7/q;.a` pc=427) runs and throws its own R8-internal exception. **A masked frontier unmasked by the anchor repair + F-C4-581 — visuals byte-faithful throughout** | W10 queue (not a rejection: the load completing is the intended direction of travel) |
| **Verdict** | all five W8 laws + nine W9 laws in-tree on my line; every acceptance grep passes; corpus battery byte-inert on every anchor measured | **W8 + W9 APPROVED + MERGED (commit on main); honest rows = stale #522 header sha + TG unmasked l9/j family** |
| **PINNED NEXT** | (1) TG `Lt7/q;.a` l9/j family (DEX-decode; the unmasked native-init frontier); (2) TK F084 deep-execution families (MINIANDROID_W9_PROBE re-census); (3) NC `resolveNetworkCapabilities` + theme/binding + NativeCrypto static-native dispatch; (4) TB `Fragment$$ExternalSyntheticLambda0` NPE; (5) CB `Platform.<clinit>` + nav-args; (6) Compose paint-color `31ddd4d5` (THE content blocker, unchanged); (7) IME harness law queued | |
