# DECISION LEDGER (append-only; speed-addendum §31)

| # | Decision | Reason | Alternatives considered | Evidence | Date | Commit |
|---|---|---|---|---|---|---|
| D-01 | Arrays.fill: keep F-040 (remote superset), dedupe F-056 (local) | identical law discovered on divergent lines; F-040 covers all primitives+Object with verbatim tags + null-NPE + WIDE-DIAG | keep both (rejected: shadowed handler = latent divergence); rebase local (rejected: keeps two impls) | merge validation: battery 91/91 + hello_color byte-identical | 2026-09-11 | 0383f19f |
| D-02 | Merge strategy = merge commit, no history rewrite | mother-repo law: never force-push/rewrite published history; M9 commit was unpushed so merge is the honest record | rebase M9 onto M8 line (rejected: rewrites the working record used by evidence) | ls-remote verified 0383f19f | 2026-09-11 | 0383f19f |
| D-03 | Credentials via GIT_ASKPASS + /home/z/.gh_token (600) outside repo | token must never enter source/worklog/evidence/logs (M9 §1) | inline URL push (rejected: token in process cmd), credential store (rejected: persists) | leak grep over repo: CLEAN | 2026-09-11 | — |
| D-04 | aapt2+ECJ+D8-built fixtures are the ARSC/AXML authority | no handwritten ARSC/AXML (audit §O/P law) | handwritten binary resources (rejected: unverifiable) | every battery fixture | standing | — |
| D-05 | No package-specific hacks ever (§28) | generic semantics only | per-APK branches (REJECTED by law) | all F-law implementations | standing | — |
| D-06 | Single-threaded logical executor laws (volatile publication within executor; weakCompareAndSet NOT_RELEVANT) | architecture choice documented; no fabricated concurrency | full thread-machine emulation (rejected: no live demand) | audit §D/K1 | standing | — |
| D-07 | LockSupport/virtual time = architecture choice, not Android law | report §15 caveat honored | | audit §E | standing | — |
| D-08 | Tool-output ≠ root-proof; screenshots are evidence not success | L-06 gossip lesson | trust report status (rejected) | pixel-count law | standing | — |
| D-09 | F-number collision resolution: repo F-053..F-057 (shape/hashCode/Long/fill/duality) keep their IDs; M9-B analysis findings (lifecycle registry, WeakReference, HashMap.values, const-class identity, check-cast proof) registered as R-NEW-279..284 instead of renumbering | prevents evidence-chain breakage; living-map law §17 | renumber M9-B findings as F-058+ (rejected: F-058 already referenced in campaign brief with different content) | ROOT_WORKLIST GROUP G | 2026-09-11 | — |
| D-10 | 278 roots must flow through shared tooling infrastructure before manual deep-dives (PHASE-0 tooling brief) | 278 independent manual tasks = architectural error (briefs §11/§48) | manual per-root investigation (rejected) | docs/agent-index + tools/verify | 2026-09-11 | — |

## S21 decisions
- **D-S21-1**: reconcile-first held — the container reset had rewound local
  HEAD to the M5 era; remote b7d654a5 was fetched and fast-forwarded before
  any analysis (no re-litigation of F-058..F-073).
- **D-S21-2**: the S21 gate interpretation ("callback removed-not-run") was
  refined, not taken as granted: upstream AndroidUiDispatcher source was
  fetched and the removal branch proven legal. Chasing the removal as the
  root would have produced a WRONG fix (a dooz-specific frame pump hack).
- **D-S21-3**: F-074 fix shape = walk at the two try_recursive_invoke give-up
  points (not a rewrite of invoke resolution) — minimal, general, and
  receiver-identity-preserving; the interpreter's own invoke path already
  walked and was left untouched.
- **D-S21-4**: F-075 fix shape = retype at the three reference-use boundaries
  (return-object, move-result-object, mixed 22t) instead of changing
  const/4 semantics globally — primitive zero must stay INT32 in primitive
  contexts (F-028/F-030 law continuity; the CHAR-PROBE/EXP-093 zero laws
  are untouched).
- **D-S21-5**: battery verdict 89/92 recorded honestly: the three failures
  are bisect-proven environmental, not waved away.
