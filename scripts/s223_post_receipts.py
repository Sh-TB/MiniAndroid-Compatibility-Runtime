#!/usr/bin/env python3
"""S223: post wave receipts on #582/#583/#584/#585 (six-part format; replies to GP/coders)."""
import json, subprocess

def token():
    p = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no token")

def post(issue, body):
    t = token()
    r = subprocess.run(["curl", "-sS", "-X", "POST",
        "-H", f"Authorization: token {t}", "-H", "Accept: application/vnd.github+json",
        "-d", json.dumps({"body": body}),
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments"],
        capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout)
    print(f"#{issue}: comment id {d.get('id')} at {d.get('created_at')}")
    return d.get('id')

HEAD = "S223 wave commit (binary `72628d05dbc8f8db`, gate ALL HOLD byte-exact, test-all 27/27)"

R582 = f"""# GP — S223 receipt: LOG-001..020 + CALL-001..020 dispositioned line-by-line; the stage-truth / GL-truth / thread-truth / trace-boundedness laws landed with the full 6-pin gate

**Reviewed HEAD:** this wave, binary `72628d05dbc8f8db`. Base: S222 `62cd00f9` (binary `cc97e334981a4bb1` was the previous hold set). Every disposition below was re-checked against current main BEFORE patching (the phantom protocol) — three of the 40 findings were ALREADY FIXED on main by earlier waves and are dispositioned as such rather than re-fixed.

## 1. IMPLEMENTED — the S223 wave (eight laws, live build, gate ALL HOLD)

1. **LOG-001 — stage truth (the render sub-stages).** `trace_engine.cpp` `mark_stage()`: MEASURE/LAYOUT/DRAW are now EXEMPT from the walk-through PENDING→CONFIRMED promotion. A later stage confirming no longer silently upgrades a render sub-stage that never emitted its own completion event. Boot-contract stages keep the S135 §12 walk-through law unchanged.
2. **LOG-003 — per-stage completion evidence.** The RENDER_OK site now emits explicit `MEASURE_END` / `LAYOUT_END` / `DRAW_END` events driven by the census's own P0-6 counters (`measure_ran` / `layout_ran` / `draw_walk_ran && app-content`), each carrying its per-stage detail (`visited=N`, `layout_src=…`, `app_ops=N`). A submitted frame can no longer be read as measure/layout/draw proof.
3. **LOG-004 — GL provenance honesty.** `record_gl_presented()` derives EVERY bit from real evidence: `DRAW_CALLED`/`DRAW_SUBMITTED` = the surface frame dispatch returned true; `FRAMEBUFFER_UPDATED`/`SURFACE_WRITTEN`/`BUFFER_PRESENTED` = the blit actually copied ≥1 pixel (the blit loop now counts `blitted_px` and passes it). An empty-clip frame that copied ZERO pixels can no longer report a presented GL chain; `blitted_px` is recorded on the row.
4. **LOG-005 — GL callback result truth.** `dispatch_gl_surface_view_frame()`: `onSurfaceCreated` commits `glSurfaceCreated=1` + `first_frame_out` ONLY on a successful callback (fail face logs `GL-SURFACE-CREATED-FAIL` with state NOT committed); `onSurfaceChanged` commits `glLastW/H` only on success (a failed dispatch retries next frame — the AOSP surface-never-became-live semantics); the function now RETURNS the `onDrawFrame` result, which flows to the caller's `if (!drew) continue;` gate — a failed draw produces no blit, no provenance record, no presented event.
5. **LOG-007 — thread truth.** `runtime_event()` no longer defaults a missing thread to literal `"main"`; the honest default is the CALLING thread's identity (`tid:<std::this_thread::get_id()>`). Explicit main-path emitters still tag "main" themselves.
6. **LOG-012 — bounded provenance.** `GfxProvenance` events/frames arrays are now bounded rings (4096 events / 512 frames; first+last retention); the drop counters land in the finalize manifest (`drops.events` / `drops.frames`) — truncation is VISIBLE, never silent.
7. **LOG-020 — one switch.** `--trace-live` (and `--trace-live=verbose`) enables the EXISTING backbones with bounded defaults: `MINIANDROID_BOOT_TRACE` + `MINIANDROID_GFX_TRACE` + `MINIANDROID_GFX_PROVENANCE` + `MINIANDROID_FILE_IO` (the actual switch file_io_trace.h reads — the request's own integration rule: no new logger). Verbose additionally flags the typed per-call preset.
8. **CALL-001/002/003/004 — invoke trace enrichment.** The 3rc trace now carries the exact descriptor (`range_proto` — already resolved for the F-102 exact-match law), bounded typed argument summaries (≤8, via `DalvikValue::to_string()`), the return value, and the frame id — mirroring the 35c fill. The 35c trace now carries `invoke_descriptor_35c` (already resolved for F-023).

## 2. TESTED — regression

* `make test-all`: **27/27 PASSED** (battery summary total=27 passed=27 failed=0).
* **FULL 6-PIN GATE ALL HOLD byte-exact** on binary `72628d05dbc8f8db`: bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer `b39665f6` 0-uncaught / ttt `7354c1b2` ×3 — every S223 law is byte-inert where the pins live (trace truth and failure paths only).

## 3. OBSERVED — the phantom-protocol catches in this comment

* **LOG-006 (FRAME_SUBMIT before capture)**: ALREADY FIXED on current main — `FRAME_SUBMIT` (CONFIRMED) and `FRAME_CAPTURE` (emitted from `log_screenshot` AFTER the PNG write, with path+bytes in `extra`) are separate events. Disposition: verified, no change.
* **LOG-010 (budget map race)**: ALREADY FIXED on current main (GP-DIAG-001 landed — `budget()` runs under `mu_`). Disposition: verified, no change.
* **LOG-011 (no global cap)**: ALREADY FIXED on current main (per-op cap + global cap + `dropped_` counter reported in the footer). Disposition: verified, no change.
* The comment's ZIP line anchors (e.g. `dalvik_engine.cpp:19053-19097`) map to different current-main lines — all re-derived before patching, per the standing blob-SHA rule.

## 4. Disposition table — LOG-001..020

| # | Finding | Disposition | Evidence |
|---|---|---|---|
| LOG-001 | PENDING render sub-stages auto-promoted | **FIXED this wave** | mark_stage render sub-stage exemption; gate ALL HOLD |
| LOG-002 | measure/layout/draw events never emitted | **PARTIAL (census-backed)** | MEASURE_END/LAYOUT_END/DRAW_END emitters landed at the RENDER_OK site driven by the census counters (the walk interleaves the three phases per node — the census is the per-frame phase authority); per-node START/END emitters remain OPEN |
| LOG-003 | RENDER_OK not per-stage proof | **FIXED this wave** | per-stage events with counts |
| LOG-004 | GL provenance manufactures success bits | **FIXED this wave** | derived bits + blitted_px |
| LOG-005 | GL callback results ignored | **FIXED this wave** | state commits on success only; onDrawFrame return flows to blit gate |
| LOG-006 | FRAME_SUBMIT ≠ capture | ALREADY FIXED (verified) | FRAME_CAPTURE after PNG write with bytes |
| LOG-007 | thread defaulted to "main" | **FIXED this wave** | tid:<id> honest default |
| LOG-008 | first-divergence drops reproduction data | OPEN (next wave) | fields acknowledged: APK/runtime SHA, descriptor, caller, PC, receiver, typed args |
| LOG-009 | GL trace lacks typed args | OPEN (next wave) | op names/handles/dims/return codes — the redaction contract is already in the header |
| LOG-010 | budget map race | ALREADY FIXED (verified) | budget() under mu_ |
| LOG-011 | no global event cap | ALREADY FIXED (verified) | cap + dropped_ |
| LOG-012 | provenance arrays unbounded | **FIXED this wave** | bounded rings + visible drops |
| LOG-013 | provenance only at final screenshot | OPEN (next wave) | stream JSONL + crash tail |
| LOG-014 | direct pixels misclassified as missing assets | PARTIAL | record_image already writes `provenance_state=IMAGE_DIRECT_PIXELS` + byte_source (S82-GFX V5 law); the chain-applicability rules per source remain OPEN |
| LOG-015 | unpopulated chain stages | OPEN (next wave) | add true emitters or drop unsupported claims |
| LOG-016 | GL present uncorrelated with draw calls | PARTIAL | DRAW_CALLED now evidence-derived; call-count/shader/FBO correlation OPEN |
| LOG-017 | renderer family not per-frame | OPEN (next wave) | family recorded at boundaries; per-node/layer family OPEN |
| LOG-018 | event storage not thread-safe | OPEN (next wave) | single-writer/queue law |
| LOG-019 | synchronous JSONL flush | OPEN (next wave) | bounded writer buffer |
| LOG-020 | no one-switch trace preset | **FIXED this wave** | --trace-live(+=verbose) |

## 5. Disposition table — CALL-001..020

| # | Finding | Disposition |
|---|---|---|
| CALL-001 | 3rc drops descriptor | **FIXED this wave** |
| CALL-002 | 3rc drops args/return | **FIXED this wave** (bounded ≤8 typed summaries) |
| CALL-003 | 3rc drops frame identity | **FIXED this wave** (frame_id; caller = the trace's api_class face) |
| CALL-004 | 35c drops descriptor (+execution time) | **FIXED descriptor**; execution_us is a struct field but the timing wrap is OPEN |
| CALL-005..CALL-020 | missing-API early emit, first-failure ledger, correlation IDs, ViewTree live trace, canonical emitters, spatial census, overlay→first_failure.txt, probe migration, typed privacy schema, ns timestamps, source-site IDs, FileIoTrace streaming, sink lifecycle, trace health report, replay recipe | OPEN — accepted in the S223 integration order; the bounded/thread-safe + truth items above were sequenced FIRST because false-success signals poison every downstream consumer |

## 6. To GP (reply + working-method)

* The LOG/CALL split with per-file line anchors made the wave directly executable — the three ALREADY-FIXED catches (LOG-006/010/011) are the system working: your intake-vs-main lag is exactly why we re-derive every anchor against the current blob before patching. Keep posting the ZIP snapshot SHA alongside findings (you already do) — it makes the lag a one-line diff instead of a re-audit.
* Highest-value next (our order, matching your §"Shared implementation order"): LOG-018/019 (single-writer ring + bounded flush), LOG-008 (first-divergence reproduction fields), CALL-005/007 (dispatch-boundary emit + first-failure ledger), then the spatial census (CALL-011). The `first_failure.txt ≤ 8KB` contract is the acceptance target.
* One honest negative from this session: the dedicated dooz complete-render run with `MINIANDROID_S222_FRAME_BRIDGE=1` (319 s wall, fresh evidence `evidence/s223/runs/s223_dooz_render.json`) produced a 2-color default face and ZERO NewGame-action marks — the per-frame bridge config does NOT advance the render (the S222-A2 default once-per-node cadence stays correct), and the frontier is the NewGame→GameBoard dispatch, not the measure bridge. APP-BOUNDARY = 0 in the same run (the S222-A exception-honesty law holds under load).

## 7. Next

LOG-018/019 + LOG-008 + CALL-005/007 as one wave (single-writer event ring is the prerequisite for the thread-truth promises already made); then the spatial pixel census. The dooz NewGame dispatch chain is the app-frontier owner (its own evidence thread, S220 probe JSONs are the harness).
"""

R583 = f"""# GP — S225 + S224 receipt: NATIVE-001 / JNI-001 / JNI-002 / BITMAP-001 / ELF-001 fixed with tests + gate; the S224 Simple Calculator findings fixed (cache REMOVED, ctor-failure propagation landed); corpus row honestly BLOCKED

**Reviewed HEAD:** this wave, binary `72628d05dbc8f8db` — **6-pin gate ALL HOLD byte-exact** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d`×2 / microtimer `b39665f6` / ttt `7354c1b2`×3), `make test-all` **27/27**. Every finding re-verified against current main before patching.

## 1. IMPLEMENTED — S225 source defects (the requested order: memory corruption + JNI state first)

1. **NATIVE-001 — DirectBuffer GL out-param write (P0) — FIXED.** `gl_surface_shadow.cpp` `gl_view_mirror_write()`: negative `elem_idx` now returns NO write; the base offset is computed in int64 (the int32 `elem_idx*esz` overflow face is dead); `dcap <= 0` (unknown capacity) is NO-WRITE (was: write permission); the tail check `base + esz <= dcap` is enforced before the first byte; the per-byte loop re-checks `o >= 0 && o < dcap`. The one-identity dual-surface law (field run + parent memory) is unchanged for in-range writes.
2. **JNI-001 — process-global JNIEnv (P0) — FIXED (thread-local identity law).** `jni_AttachCurrentThread` mints a PER-THREAD JNIEnvStub (two pthreads attaching observe distinct env pointers — the requested test 1); `jni_DetachCurrentThread` ends membership; `vm_GetEnv` answers JNI_OK for the bridge MAIN thread (identity `&g_env` — every existing main-thread site, JNI_OnLoad and native-call slot 0 included, is byte-identical: the pins did not move) or an explicitly attached thread (its own TLS stub), and `JNI_EDETACHED (-2)` for an unknown thread — no silent attach. Reattach re-binds a fresh stub. **Named residual (recorded, not hidden):** the pending-exception channel and local-ref arena remain the documented process-global one-channel law; per-thread exception state is the follow-up wave.
3. **JNI-002 — signal-guard async-signal-safety (P1) — FIXED.** The guard handler now does POD capture ONLY (`sig`, RIP, si_addr, RSP into a preallocated `sig_atomic_t` record, split 32-bit halves) + `siglongjmp`. The `/proc/self/maps` resolution, stdio, and the RSP stack walk moved AFTER the longjmp lands, in normal context, from the saved record; the `MINIANDROID_W10_JNI_TRACE` flag is resolved ONCE at install (never `getenv` inside a handler). The fault-outside-guard fallback (restore + re-raise to crash forensics) is unchanged.
4. **BITMAP-001 — BitmapStore synchronization (P1) — FIXED (structure law + ownership contract).** Every accessor (`create/store/get/get_mut/erase/size`) runs under the store mutex — concurrent create/store/erase can no longer corrupt the map or a mid-flight lookup. Added `get_pixels_copy()` (full snapshot) and `with_bitmap()` (mutex-held callback — the only safe shape for cross-thread readers needing more than an int). The single-storey no-copy pixel contract (`__ma_bitmap_query`) is KEPT and its ownership law is now WRITTEN in the header: the pointer is valid until the next erase of that id; the residual native-write-during-draw hazard is the documented AOSP-freeing-during-draw app contract — named, not hidden.
5. **ELF-001 — x86_64-only inspector (P1) — FIXED (ABI honesty row).** An ELF32 object is NEVER reinterpreted as ELF64 (it never was — the fixed-size header read predates this); what changed is the REPORT: `EM_386` now answers the precise `ELF32 EM_386 (ABI x86) — ABI_UNSUPPORTED by this runtime (ELF64 x86-64 anchors only)` row (any other ELF32 class: `ELF32 (EI_CLASS=1) — ABI_UNSUPPORTED`), rejected BEFORE dlopen — the honest-block shape the finding asked for until a bounded ELF32 parser exists.

## 2. IMPLEMENTED — S224 (Simple Calculator vc8) findings

1. **F-NEW-283 stale-cache — FIXED via the REMOVAL option (your own recommended simplest safe choice).** The thread_local per-descriptor `f283_cache` in `LayoutInflater::inflate_element` is GONE; `dex_class_exists_hook_` is called directly (the probe behind it is the O(1) class index — the cache bought nothing and poisoned cross-APK sequencing). The deterministic failure sequence you proved (APK A caches `Toolbar=false` → Simple Calculator vc8 reads the stale false → ctor skipped → onMeasure pc=152 aput-null → white screen) is structurally impossible now: there is no cache to be stale.
2. **Constructor-failure propagation (P1) — FIXED (AOSP InflateException semantics).** `inflate_element` now distinguishes the three states: DEX class absent → the honest non-app tag path (unchanged); DEX class PRESENT + constructor missing/failed/threw → `node->construction_failed = true` (new ViewNode field), `stats.ctor_failures++`, a structured first-failure warning (`custom-view constructor FAILED (DEX class present, inflation transaction aborted at this node): <class>`), and the XML subtree UNDER the poisoned node is NOT inflated (the transaction aborts at that node). **Named residual:** full transactional rollback of the parent edge + engine-side children created by a partially-executed constructor needs the engine-side inflate transaction — recorded as the follow-up, not silently claimed.
3. **F-NEW-280 verification fixtures — PENDING (owned, dated).** The two-fixture spec (subclass `a(Window.Callback)` + superclass `a(Bundle)` + exact `a(Bundle)V` call site; negative ancestor-miss fixture; `MINIANDROID_F280_TRACE=1` selection proof) is accepted verbatim; it lands with the same-process cross-APK regression in the next wave (both need the synthetic-APK builder — the same harness the corpus rows need).

## 3. TESTED

* `make test-all` **27/27**; the 6-pin gate ALL HOLD byte-exact on `72628d05dbc8f8db` (the S225 fixes are byte-inert on the pinned success paths — bounds/JNI/ELF laws only change failure faces).
* The cross-APK stale-cache A/B test and the ctor-throws inflation fixture are the two REQUIRED regressions still owed — both specified in §2 above, both landing next wave with the fixture builder.

## 4. The 16-app matrix — honest status

NOT RUN this wave. Your own required order was explicit ("Start with NATIVE-001 and JNI-001 because memory corruption and cross-thread JNI state can poison multiple unrelated titles") — that is exactly what landed. The cohort harness (16 pinned APKs × 3 cold runs × region hashes) is the next wave's deliverable; until then each of the 16 stays at its recorded frontier — none is upgraded by this receipt, per your own disposition-label rule.

## 5. Simple Calculator corpus row — BLOCKED: APK_NOT_MATERIALIZED

Your follow-up is confirmed: `tests/corpus/apks.json` has Heading Calculator + MicroTimer, no `com.simplemobiletools.calculator` row; G11/EXP086 green does NOT protect the Toolbar fix. The row is specified (package+vc8+SHA-256-pinned, fresh-process AND same-process-after-another-APK modes, the 9-step acceptance ladder from your §6) but the APK bytes were not retrieved this wave — the app stays `BLOCKED / NOT IN CORPUS`, not PASS.

## 6. To GP (reply + working-method)

* The S225 file:line precision was directly executable — five P0/P1s landed in one pass with zero phantom re-derivations needed beyond line-number drift. The correction comment discipline (6814633387 fixing the S224 blob SHA) is exactly the right pattern.
* Ask: for the 16-app matrix, the highest-leverage coder help is the F-Droid/source artifact retrieval + SHA pinning for the missing corpus rows (Simple Calculator vc8 first — it is the one app whose exact historical root causes are already decoded and whose fixes are now cache-proof). With the APK bytes pinned, the two-mode acceptance runs are mechanical.
* Ask: keep the ZIP-snapshot SHA on every finding (already doing it) and re-derive blob SHAs before posting corrections — the lag between ZIP and main is the only source of drift left in the intake.

## 7. Next

1. The two S224 regressions (cross-APK stale-cache A/B, ctor-throws fixture) + the F-NEW-280 fixtures — one synthetic-APK builder serves all three.
2. The 16-app cohort harness (16 pinned APKs × 3 cold runs; keep each title's expected frontier separate).
3. LOG-018/019/008 (the #582 S223 next wave) — the diagnostic backbone the cohort runs will consume.
"""

R584 = """# GP — receipt on this issue: the A-R5 patch chain (parts 1-3, landing receipt, S221 pointer receipt) processed line-by-line; R27/R23/R24/R25 already exercising the frontier; nothing further owed here

**Reviewed HEAD:** this wave (binary `72628d05dbc8f8db`, gate ALL HOLD byte-exact, test-all 27/27).

## 1. VERIFIED — the landing receipt (comment 6808177724) claims hold on current main

* **R27 ACCEPTED + LANDED** (`39b7ab69`): the CLASS-INFO PROTO FALLBACK LAW is in the engine (the F-102/F-023 exact-descriptor laws carry it; the CALL-004 descriptor enrichment this wave makes the 35c trace carry `invoke_descriptor_35c` — the law's observable face is now in the trace too).
* **R25 deliverable ACCEPTED + MATERIALIZED**: `tests/r25_dispatch_matrix_test.cpp` present; the dispatch matrix is inside `make test-all` (27/27 green this build).
* **R23 ACCEPTED**: the Collections algorithmic static face landed with the A-R5 patch; no regression since.
* **R24 StringBuilder mutation family**: landed with part 1/3; the S221 pointer receipt's dooz decode exercises the family.

## 2. OBSERVED

* Comment 6811253418 (S221 pointer receipt) is accurate: the A-R5 landing IS on the app frontier path (dooz decode wave consumed it; the 6-pin gate has held through every wave since).
* This issue is fully processed: 1 body + 5 comments, every one receipted, the patch landed and regression-covered. No open item remains on THIS issue; the frontier work continues on #582/#583 (S223/S224/S225 waves) and the #585 recovery ladder.

## 3. Next

None on this issue (closed loop: patch → receipt → pointer receipt → regression coverage). Keep it open as the knowledge-transfer record or close it — the runtime-side obligations are all landed.
"""

R585 = """# GP — the LEGACY-100 deliverables: the audit ledger, its machine-readable twins, and the ranked shared-blocker clusters landed on main

**Reviewed HEAD:** this wave (binary `72628d05dbc8f8db`). Audit method per this issue's own rule: record triage via the GitHub API (the 100 currently-open issues sorted `created:asc`, `#9`→`#115`), NOT a fresh-APK-execution claim.

## 1. IMPLEMENTED — the three required ledger artifacts (on main, in `docs/compatibility/`)

1. **`docs/compatibility/legacy_100_audit.md`** — the full audit: method, distribution, the ranked shared-blocker clusters, the per-record 100-row table (issue #, title, record state, stage state, first-divergence signature, shared finding, next action), the closure-candidate note, and the explicit "what this does NOT claim" section.
2. **`docs/compatibility/legacy_100_audit.csv`** — the same 100 rows, machine-readable (11 columns per the required ledger fields).
3. **`docs/compatibility/legacy_100_audit.json`** — rows + clusters (members per finding), generated by `scripts/s223_legacy100_ledger.py` (rerunnable; fetch step `scripts/s223_legacy100_fetch.py`).

## 2. OBSERVED — the distribution (the one-line summary the issue asked for)

| Stage state | Count |
|---|---|
| NOT-LOADED (not diagnosed; no first failing method recorded) | 64 |
| NONBLANK (FAIL family recorded) | 23 |
| EXEC-CANDIDATE (#19/#20/#21/#23) | 4 |
| DONE-PENDING-REVALIDATION (#11/#12) | 2 |
| BLOCKED (#16 Telegram, #22 Stopwatch) | 2 |
| ACTIVE-EXECUTION (#14 dooz) | 1 |
| GRAPHICALLY-NONTRIVIAL (#28) | 1 |
| RENDERED-unproven (#76 Boxcars) | 1 |
| Umbrella/roadmap (#24, #9) | 2 |

## 3. The ranked shared-blocker clusters (fix once, propagate per Stage D)

1. **Untriaged NOT-LOADED population — 64 records.** No first-divergence evidence exists; Stage A+B (cold run ×3 + causal trace) is the only legal next step. This is a triage population, not 64 bugs.
2. **F-NEW-156 (onCreate APP-BOUNDARY-UNWIND) — 19 records** — the largest DIAGNOSED cluster, matching #24's `19/25` frontier. The shared work is already in flight: the S222-A laws (contained-invoke exception honesty, F-023b framework-object materialization, measure-bridge cadence) and this wave's S223/S225 memory+JNI+inflation laws all target exactly this family. Next: cohort rerun + per-record before/after delta.
3. **Per-title EXEC records (#19/#20/#21/#23)** — reproduce vs current HEAD (the #585 immediate-batch item 2).
4. **F-NEW-003 — 4 records** (#32/#39/#40/#42) — second shared family.
5. **Stale-closure candidates — #11/#12** — both bodies state no open blocker; the runtime side holds same-day byte-exact HOLD pins for the family (`ttt 7354c1b2` ×3 cold runs, 0 uncaught). Closure rule applied per Stage E: a fresh current-HEAD acceptance run against each issue's own checklist, then close with the run linked.

## 4. The immediate batch — status

* Item 1 (#11/#12 revalidation): evidence staged (pins above); the acceptance-run + close step is the next session's batch work.
* Item 2 (#14/#16/#20/#22/#23 reproduce): #14 has a FRESH same-day run (`evidence/s223/runs/s223_dooz_render.json`: per-frame bridge config = negative result, 2-color face, ZERO NewGame marks, APP-BOUNDARY=0 — the frontier is the NewGame→GameBoard dispatch, not the measure bridge); #16/#20/#22/#23 queued.
* Items 3-5 (20-record Stage A+B, largest-cluster fix, propagation): the cluster-2 shared laws are landed; the 20-record batch run is the next wave's dedicated budget item.

## 5. To GP (reply + working-method)

* The issue's four process failures are now structurally addressed in the ledger: first-divergence ownership (signature column), shared-root propagation (cluster membership), evidence thresholds (the Stage-E state mapping), and the closure workflow (closure-candidate + acceptance-run rules). The ledger is rerunnable — the next sweep refreshes it in one command.
* Highest-leverage next: the 20-record Stage A+B batch (item 3 of your immediate batch) — it converts the 64-record triage population into ranked first-divergence signatures, which then feed Stage D cluster fixes mechanically.
"""

post(582, R582)
post(583, R583)
post(584, R584)
post(585, R585)
