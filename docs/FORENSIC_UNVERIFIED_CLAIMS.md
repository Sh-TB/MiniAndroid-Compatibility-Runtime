# FORENSIC UNVERIFIED CLAIMS (issue #365)

Definition (#365 §2): previously claimed complete, but adequate evidence cannot
be found. These rows are NOT converted to VERIFIED merely because a related
commit exists. Each entry states the exact missing evidence.

## U1. Telegram journey document — UNVERIFIED_CLAIM (FR-NI-006)

- Claim: "The complete English journey document is now live" (#355 comment,
  2026-09-29) via `preview-chat-…space-z.ai/downloads/TELEGRAM_JOURNEY_S117_S119.md`.
- Finding: the preview host link is dead and `TELEGRAM_JOURNEY_S117_S119.md`
  was never committed to the repository (searched: zero hits).
- Missing evidence: an in-repo copy of the document (the issue-comment text is
  preserved but is not the claimed artifact).
- Status impact: FR-357–363 knowledge-transfer rows stay VERIFIED only as
  issue-body documentation, E2.

## U2. ROOT-062..067 + S102-A..D exist in NO registry (FR-NI-007, FR-349..352, FR-355/356 legs)

- Claim: Telegram chain roots recorded as fixed (errors 32→0, billing chain,
  StaticLayout.Builder, created-phase fan-out, payload-int cycle identity,
  UTF-16 length law, collection-view size truth, ArrayDeque routing).
- Finding: `root_registry.json` (530 roots) contains F-NEW-231/234 and
  R-NEW-457 but NOT ROOT-062..067 nor S102-A..D; the canonical projection
  `canonical/root_cause_registry.json` (492) also lags `root_registry.json`.
- Missing evidence: registry rows with commit + trace refs for these IDs; a
  regenerated canonical projection.
- Status impact: those roots stay TESTED/OBSERVED at E3/E4 (issue-comment
  diffs + run tables), never VERIFIED.

## U3. Checked Telegram goals G1–G18 — OBSERVED, not VERIFIED (FR-NI-003-G*)

- Claim: checkboxes `[x]` in the 190-goal roadmap (#363 §3).
- Finding per #365 §11 ("do not trust checked boxes"): G1–G10 are environment
  claims recorded in session notes; G11–G17 carry diffs/run tables in #356
  comments; G18's inventory is referenced but the committed inventory file was
  not located by this audit.
- Missing evidence: re-execution at current HEAD under the pinned protocol
  (`scripts/s117_tg_run.sh`), and the committed official-APK inventory.
- Status impact: all 18 rows OBSERVED/E3.

## U4. Micro-gap CLOSED/ALL-PASS labels — synthetic class (FR-234..333)

- Claim: 79 CLOSED + 131 TESTED in MICRO_GAP_REGISTRY.
- Finding: evidence strings are battery/gate stages (`docs/testing/
  BATTERY_INDEX.json`, synthetic fixtures). Under #365 §6/§23 a passing
  synthetic test is NOT real-APK compatibility proof.
- Missing evidence: per-ticket real-APK fan-out demonstrations.
- Status impact: capped at TESTED/E2 (or OBSERVED/E3 where a runtime face was
  captured).

## U5. 202-title corpus reports — mostly PENDING (FR-024 + FR-025..226)

- Claim: 202 per-title "compatibility report" issues.
- Finding: frozen title registry records 161 NOT_TESTED / 41 EXECUTED;
  96 titles appear in NO registry at all; 4 BLOCKED_DOWNLOAD_FAIL.
- Missing evidence: executions + per-title records, or honest closure of the
  report issues as not-run.

## U6. Stale `.agent` law files (found, recorded; not itself a claim)

- `.agent/state.md` still describes the EXP-090 campaign (HEAD 1fed509);
  `.agent/master_campaign_state.md` still describes D05-Resources with
  NOT_STARTED rows that are long finished (D07/D08).
- Missing evidence: none — this is a documentation-truth gap; current truth
  lives in CAMPAIGN_STATE.md + worklog. Recorded so a future reader does not
  treat the stale files as law.

## U7. Knowledge-transfer scripts committed? PARTIAL

- #361 claims "full source of all six reproduction scripts" in the issue body.
  The repo carries many `scripts/s1*.sh` artifacts, but a 1:1 mapping of the
  six quoted scripts was not verified file-by-file in this pass; treat the
  issue-body copies as the canonical record until cross-checked.
