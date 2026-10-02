# FORENSIC CLAIMS vs EVIDENCE (issue #365)

Campaign: MASTER FORENSIC VERIFICATION. This report answers: **"After auditing all
prior requests, how much of what was claimed as done is actually proven today?"**

Method: the full request corpus (365 GitHub issues + 708 owner comments + 597
commits + 7 registries + worklog/`.agent` laws) was reconstructed into ONE
canonical ledger (`FORENSIC_ALL_REQUESTS_LEDGER.jsonl`, 390 rows). Every row
carries `claimed_status` (what the record says) and `verified_status`
(independently determined under the #365 §2 vocabulary). "Done" statements from
prior sessions were treated as claims, never as evidence. Statistics in §B are
computed from the ledger file, not estimated.

## A. Executive truth report

**Roughly two thirds of the claimed work survives as real, evidenced
engineering — but only a small core reaches the full VERIFIED/E5 standard, and
the largest single block of "requests" (the 202-title F-Droid corpus reports)
is predominantly PENDING by the project's own registry.**

Concretely:

1. The **runtime foundation claims are real**: 530 registered roots; the root
   fixes that were spot-audited (F-NEW-165/167/170, F-NEW-231/234, R-NEW-457)
   carry commits, tests and traces. The canonical evidence validator passes
   R1–R12 with 0 FAIL after this campaign closed 3 sync FAILs.
2. The **loading campaign's claimed P0 scope is genuinely verified at current
   HEAD**: during this forensic campaign the gates were re-run independently —
   `working_vs_failing_probe.sh` 5/5 goldens byte-identical ×3,
   `loading_probe_runner.sh` 23/23, a NEW uninstall proof 16/16 — all at HEAD
   `438f8e85`+fixes. This is E5-class, reproducible evidence.
3. The **Telegram claims are PARTIAL, not complete**: the 0-error execution
   parity (official + forkgram), the ROOT-064..067 law diffs, and the first
   login-pixels/Dialogs-page records are documented with run tables in issue
   comments; but the full login display is NOT achieved (z-order overpaint
   frontier is honestly recorded), and ROOT-062..067 were never entered into
   any registry.
4. The **202-title compatibility-report corpus is mostly not executed**: the
   frozen title registry itself records 161/202 NOT_TESTED, 41 EXECUTED. The
   issue titles implied per-title compatibility reports; the honest state is
   122 PENDING rows in the ledger.
5. **Micro-gap tickets (100 issues + 311 registry tickets) are synthetic-class
   evidence** (battery/gate, E2). Under #365 §23 that is NOT real-APK
   compatibility proof; they are classified TESTED/OBSERVED at most.
6. **One UNVERIFIED_CLAIM was found and recorded**: the Telegram journey
   markdown was published only on a now-dead preview host and never committed;
   its content survives only inside issue comments.
7. **README/homepage honesty is broadly real** (strict vocabulary, no
   full-compatibility claims, blank-frame law respected), but this campaign
   found and fixed a real sync gap: the canonical-evidence validator had 3
   FAILs (duplicate + 2 unregistered artifacts) and the README/ACHIEVEMENTS
   totals had drifted from the registry (148 vs disk truth → now 150, verifier
   0 FAIL).

## B. Exact statistics (from docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl, 390 rows)

| Status (365 §2 vocabulary) | Rows |
|---|---|
| VERIFIED | 30 |
| TESTED | 82 |
| OBSERVED | 105 |
| PARTIAL | 43 |
| PENDING | 122 |
| BLOCKED | 5 |
| SUPERSEDED | 2 |
| UNVERIFIED_CLAIM | 1 |
| REGRESSED | 0 |
| **Total reconstructed requests** | **390** (365 issues + 25 non-issue rows incl. 18 checked Telegram goals, 7 chat-direct/master rows) |

Evidence levels: E0=122, E1=6, E2=112, E3=87, E4=50, E5=13.

REGRESSED = 0: the two historical SHA drifts found (S114→S117 sandbox anchors;
forkgram V10→F-NEW-226/227 text laws) were recorded **justified re-baselines**
with written reasons at the time — they are law/environment changes, not silent
regressions. Current-HEAD gates all pass.

## C. Verified achievements (evidence-backed only)

The 30 VERIFIED rows are enumerated with their evidence chains in
`FORENSIC_VERIFIED_WORK.md`. Headlines, each re-verified at current HEAD during
this campaign:

- Loading-campaign P0 class: ONE path law, write/read File+Context family,
  asset contract (missing → FileNotFoundException at both sites), FD/PFD/AFD
  real-fd layer, decodeStream/decodeFile, prefs atomic+escaped+honest-commit,
  real WAL + single databases_dir, provider install stage, Intent.getData
  identity, host-escape closure (commits 26e03696 → 81134ac5 → 438f8e85).
- Golden regression set: opencalc/chess/dooz/microtimer/unote byte-identical ×3
  at HEAD (2026-10-03, this campaign).
- Installed-identity store model (F-NEW-231/234): install/list/run/pkgaudit
  from identity, source APKs hidden, plus — NEW this campaign — the recorded
  PENDING `uninstall` row closed with a 16/16 runtime proof
  (`scripts/forensic_uninstall_proof.sh`).
- Canonical GIF/achievements chain for the verified titles (Snake Deluxe,
  2048, Mini Tetris, Fish Rings, Mini Browser ×2, dooz, unote, microtimer,
  bouncy, opencalc, chess, …) with 0-FAIL validator.

## D. Unverified claims (previously "done", inadequate evidence)

See `FORENSIC_UNVERIFIED_CLAIMS.md`. Major classes:

1. Telegram ROOT-062..067 + S102-A..D — exist only in issue comments/worklog;
   not in any registry (registry coverage gap, FR-NI-007).
2. Knowledge-transfer documents (#357–363) — content is in issue bodies; the
   external journey-doc link is dead (FR-NI-006).
3. All 18 checked Telegram goals remain OBSERVED/E3 (session-bound), not
   VERIFIED, because they were not re-executed under the current HEAD.
4. Micro-gap CLOSED/TESTED labels — synthetic-class only.

## E. Regressions

None found at HEAD (see REGRESSED=0 above). `FORENSIC_REGRESSION_STATUS.jsonl`
records the 4 current-HEAD gate results + 2 historical justified re-baselines.

## F. Remaining blockers (concrete)

- S-2 dlopen/JNI native libraries; S-4 content:// query/Cursor; S-11 split
  APKs; SELECTION_FROZEN (config/density/fonts selection); S-10 localStorage;
  ST-10 sqlite/font provenance — the loading campaign's own honest frontier.
- Compose frontier (S102-B), Hilt DI (S102-C), libGDX/EGL (F-NEW-157).
- 96 corpus titles with zero registry records; 4 BLOCKED_DOWNLOAD_FAIL.
- Safir / Black sentinels: BLOCKED-BY-IDENTITY (zero project records).

## G–J

Generic fixes with fan-out proof, working-vs-failing explanation, the evidence
map and the continuation queue are in the final completion ledger posted to
issue #365 and in `FORENSIC_VERIFIED_WORK.md` / `FORENSIC_MISSING_EVIDENCE.md`.
