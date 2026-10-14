# CONT-18g — FINAL SOURCE REVIEW (the "found but never fixed" sweep + cumulative impact)

Directive: sweep comments (issue threads), archives, and the source itself for
findings that were STATED but never fixed or registered; then deliver the final
review with the cumulative source-code impact.

Binary lineage this wave: `8ee839e718877216` (recorded CONT-18) → clean rebuild →
fix family applied → **`be95a47f797d3d99`** (f268/269 fixes).

---

## 1. The sweep (what was mined)

| Source | Result |
|---|---|
| GitHub issues #353–#381 bodies | fetched fresh via HTML (`scripts/cont18g_fetch_issues.py`) |
| Issue comment threads | GitHub now renders comments via JS; API rate-limited (403, recorded honestly — same discipline as prior waves). Local archives mined instead: `evidence/cont17/github_trailing_comments.json` (issues #375–#380 full bodies), `forensic_data/issue_*_comments.json`, `tmp/comment_*.md`, `tmp/issue*.html` |
| **Issue #381** (20.7k chars, created after the last comment snapshot — **never audited before**) | the complete claims audit — every claim individually dispositioned below |
| Engine source TODO/FIXME sweep | 4 hits, all noted/closed in-code (application_context DEX-loading TODO, TextWatcher dispatch TODO, packed-switch note, FIX-05 residual closed) |

## 2. Issue #381 claims → dispositions (the decisive table)

Every "found but never fixed" claim, verified against the CURRENT source, then
fixed / refuted / documented. No claim left floating.

| #381 face | Source-verified state before this wave | Disposition NOW |
|---|---|---|
| aget on zero-length array fails to raise AIOOBE | **REAL** — `arr_len==0` treated as "length unknown", warn-and-continue null | **FIXED (F-NEW-268b)** — recorded length (even 0) is authoritative → AIOOBE; unknown-length legacy gate preserved strictly |
| aget on null → correct NPE | **REAL** — silent default; aput had the arm, aget didn't (asymmetry) | **FIXED (F-NEW-268a)** — `aget-null` NPE arm mirroring aput |
| iget on null → correct NPE | **REAL** — silent field default | **FIXED (F-NEW-268d)** — both iget and iget-object; ART order (resolve field → null check) |
| new-array negative size → exception | **REAL** — silently clamped to 0 | **FIXED (F-NEW-268c)** — NegativeArraySizeException |
| `throw` of null / unknown-class dispatch | **REAL** (new face exposed by the probe itself: ECJ folds provable-null derefs into `athrow` of the null register) | **FIXED (F-NEW-268e)** — JLS 14.18 throw-null → NPE |
| Two String.split handlers; divergence; empty-delim hang; trailing empties | **REAL** — invoke layer hung on empty delim; bridge layer answered whole-string; no `\Q..\E` parity; trailing empties retained in both | **FIXED (F-NEW-269)** — law parity in both layers (quote-strip, per-char empty-delim, trailing-empty removal); single-implementation refactor DEFERRED (mechanical, no semantic delta) |
| `class_to_superclass_.find` result used without `end()` check | **REFUTED** — all 32 call sites guarded (the one candidate is guarded with the check past a 4-line window) | REJECTED with source evidence |
| write_v silently discards OOB writes | **REAL but by-design** — documented "Bounds-safe: write_v ignores out-of-range registers"; register OOB = verifier violation upstream, not an app-visible semantic law | DOCUMENTED-DESIGN (stays; not a runtime root) |
| monitor-enter/exit unreviewed | **REAL no-op** — documented single-threaded design ("no-op in single-threaded runtime"); contention impossible; null-ref NPE arm folded into the F-268 family as a pending low-priority face | DOCUMENTED-DESIGN + F-268 pending face |
| Recomposer pumping, SurfaceView/GL incomplete, libGDX createGLSurfaceView, multi-Activity splash screenshot, WhatsApp AppContext null, SlidingUpPanelLayout gravity, Fossify Notes | already registered (R-NEW-294/340/349, F-NEW-157/162/209/211/213, R-NEW-384/388/389, F-NEW-168, R-NEW-441, R-NEW-463) | NON-FLOATING (registry rows) |
| Simple Calculator u0(Iterable) null source "unresolved at checkpoint" | superseded by lineage: split fix + F-NEW-160 field-identity + collection laws closed the recorded chain; SimpleCalc not in current corpus (artifact-dependent) | SUPERSEDED-BY-EVIDENCE |
| §F "3.7% of C++ source reviewed — complete-review claim unsupported" | **ANSWERED this wave** — see §4 coverage review | ADDRESSED |
| Claims 116–127 "require independent regression tests" | **DONE** — `fixtures/f268_exception_probe` 12/12 at `be95a47f797d3d99` | ADDRESSED |

## 3. Cumulative source-code impact of the campaign (the "تاثیر کلی")

**Engine code delivered by the whole lineage (CONT-8 → CONT-18g), all generic,
all live-verified:**

| Family | Laws/fixes | Layer (file) |
|---|---|---|
| Composition/navigation | F-256→F-265 chain proven; F-NEW-259 iterator descriptor-slot fallback, F-NEW-259b addAll append law | dex/ + framework/ |
| Collection semantics | F-264d LAW-A..F (remove-by-index coherence, iterator write-back, Java-8 default-method family, deque order, map defaults, subList view + stream pipeline) — **fcol 3/18 → 18/18** | android_shadows.cpp |
| **NEW: exception semantics** | **F-NEW-268 a–e (null/zero-length/negative/throw-null family)** | **dalvik_engine.cpp** |
| **NEW: string split laws** | **F-NEW-269 (dual-handler parity)** | **dalvik_engine.cpp** |
| Input pipeline | F-117 scheduled taps, R-NEW-394 dialog routing, S129 swipes, F-NEW-199 interaction manifest | touch_dispatcher.cpp |
| Identity/hierarchy | F-141/F-266a null laws, F-254 hierarchy composition, F-181 array identity | dalvik_engine.cpp |
| Diagnostics (env-gated, read-only) | CL-TRACE, FIELD-TRACE, F259-TRACE, S36-AOOB, S24-GETCLASS | engine-wide |
| Infra | **pre-push guard empty-list defect fixed + permanent selftest law** (was recorded twice, never fixed) | scripts/security/check_secrets.sh |

**Registry**: 576 → **578 rows** (+F-268, +F-269 both ROOT-CAUSED-FIXED; 323
terminal / 255 queued, ranked in `evidence/cont18f/findings_queue.md`).

## 4. Opcode-semantics coverage review (answering #381 §F with data)

The claims-audit flagged that opcode families were "not fully reviewed". Current
state of the exact families it named (dalvik_engine.cpp interpreter switch):

| Family | State |
|---|---|
| invoke-* (virtual/super/direct/static/interface + /range + default-method) | handled incl. F-141 null gates, F-266a default-method route, memoized dispatch |
| aget/aput (all 7 type variants each) | handled — **now with full ART null + bounds laws (F-268)** |
| iget/iput + sget/sput (all width variants) | handled — iget now with the F-268d null law; sget/sput family has F-154/F-215/216/245 rows |
| new-array / filled-new-array / fill-array-data | new-array **now with the F-268c negative-size law**; filled-new-array handled (F-181 identity); fill-array-data handled at the payload walker |
| throw | **now with the F-268e throw-null law** |
| monitor-enter/exit | documented no-op (single-threaded design); null arm = F-268 pending face |
| const family (incl. the F-028e 31i fix) | handled |
| switch payloads (packed/sparse) | handled |

## 5. Regression proof at the fixed binary `be95a47f797d3d99`

| Gate | Result |
|---|---|
| f268 exception-semantics probe (new) | **12/12 PASS** |
| Anchors (dooz/microtimer/unote/gmdice/opencalc/chess) ×3 | **18/18 MATCH byte-identical** |
| fcol collection probe | **18/18 PASS** |
| f259 iterator probe | **7/7 PASS** |
| f259g shadow probe | **12/13** (row-L = recorded CLOSED-AS-DOCUMENTED expectation artifact, unchanged) |
| f266 null/default-method probe | **6/6 PASS** |
| Negatives battery | **19/19 PASS** (after the gate_a probe-run stage was executed — the interim 9/19 was the missing probe_store stage, environment, not engine) |
| Reinstall matrix | **8/8 PASS** |
| Skill selftest | **13/13 PASS** |

Honest note: the gate_a probe APK was rebuilt in this container (libprobe
sha16 `ad413625925ed8e5` = the recorded value; apk-level sha differs from any
frozen value because probe zips are not cross-container byte-deterministic —
probe ROWS are the contract).

## 6. What remains open (non-floating, ranked in the queue)

- **P0 frontier**: F-NEW-265 (dooz measure-pass death) → F-NEW-267 (Compose tap
  hit-test gap, gates T-09/T-10) — the main line of the CONT-18 campaign.
- F-268 pending face: monitor-enter/exit null-ref NPE arm (low priority).
- F-269 deferred cleanup: single shared split implementation (mechanical).
- The 255 queued rows (P0 32 / P1 53 / P2 65 / P3 105) — every one visible,
  prioritized, dispositioned. Nothing abandoned-unused.
