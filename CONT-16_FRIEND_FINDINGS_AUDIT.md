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
