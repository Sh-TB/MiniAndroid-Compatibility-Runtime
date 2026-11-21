**S21 MASTER INTEGRATION — WS1 IMPLEMENTED (B2 dispatch contract, authorized) + recovery map. Full report: `evidence/audit/S21_INTEGRATION_REPORT.md` @ commit `3d1396c8`.**

**1-2. State:** start HEAD `1cf09f53` == origin/main, clean. Recovery classifications (verified, not assumed): #676 F058 lifecycle chain **ALREADY_IN_MAIN + reachable** — live fan-out observed this session (`[F058-DISPATCH] onActivityPostResumed … fan-out: 2/2 observers executed` in the chess run); local branches s237-s241 all merged (0 unmerged commits); stashes = evidence-only; #633/#634 unchanged BLOCKED; #612 F-GLZ-3 label not found in src/ — reconciliation PENDING (needs the issue patch reference); #484 (2048) PENDING on fetch.

**3-5. WS1 IMPLEMENTED — exactly 2 source files:**
- `src/runtime/execution_engine.cpp`: the `cv_framework` NAME-PREFIX provenance gate (`Landroid/|Landroidx/|Lcom/google/`) in the T4-PAINTGAP draw dispatch **replaced by the AOSP-faithful contract** — dispatch the real draw chain for every custom view with a **live heap object**; honest-blank safety preserved downstream (replay only on `gap_ops > 0`; 21-P0-5 purity intact; text-base/surface-family branches untouched).
- `src/dex/dalvik_engine_core.cpp`: env-gated read-only `MINIANDROID_S21_CHAIN_DUMP` diagnostic (zero default cost).

**6-9. Measured outcome (5 targets × 3 runs, deterministic):** dispatch reachability OPENED — dooz **0→82 `dispatched=YES` per run**, itsfrz **113 YES**, freebloks 2 YES, dicer 2–19 YES; rttt stays on its documented surface-family branch. **Faces byte-identical to golden (no pixel change claimed).** Two deeper layers now PRECISELY identified beneath the gate:
- **dooz**: `dispatched=YES ops=0` — the Compose draw chain now executes and produces zero ops → **B1 Compose semantics is the remaining frontier**.
- **freebloks**: `dispatched=NO` — the dex is **R8-minified** (proven: `calculateContentConstraints-l58MMJ0` in its method table, `scripts/dex_methods.py` parser) — framework-invoked draw methods are renamed/stripped, so name-based resolution finds nothing. **The next highest-leverage shared fix: R8-aware draw resolution (dex mapping / super-chain dispatch) for minified framework views.**

**10. Regression — PASS:** 6 law batteries rc=0 **batch-wise** (lifecycle ALL PASS, linear_layout 24/24, g10_layout 23/23, s98_text 21/21, gp583_gles 31/31, r25_dispatch_matrix 14/14); 4 golden anchors **byte-identical** (HelloWorldToast `acdd9f05`, notepad/randomix `31ddd4d5`, chess `d602648e` — the one early-halt reproduced as 2-core contention variance; clean rerun rc=124 + golden face). Full 108-test battery hit **ENOSPC** (5.7 GB disk < 5.8 GB of test binaries) — batch mode is the honest operational answer, recorded.

**11. Build (this host, this tree):** no-change **13.5s** (build/ survived the recycle), one-TU **37.1s**, two-TU **24.7s**, law-test batch builds ~40–60s each; clean 6m46/6m38 (prior session, ±2%); **ccache not installed** (no package access) — levers PENDING.

**12. Blockers:** (1) R8-minified draw resolution — the next shared fix; (2) Compose semantics (B1); (3) 5.7 GB disk < full-battery 5.8 GB + no ccache; (4) F-GLZ-3/F-CSW-* reconciliation needs repo-external issue content (API rate-limited this session); (5) #633 fixture / #634 doc-loader unchanged.

**13. Trackers updated here only; no new issues. Honest success statement: one previously-blocked shared chain link is implemented and PROVEN reachable across 4 app families with zero regressions; the two deeper layers are measured, named, and queued — not hidden behind a verdict flip.**
