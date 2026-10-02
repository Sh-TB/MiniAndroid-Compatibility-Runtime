# FORENSIC MISSING EVIDENCE (issue #365)

An actionable inventory of missing evidence, ordered by fan-out and evidence
value. Each row: what is missing, where it would come from, and the affected
ledger rows.

## M1. Registry rows for the Telegram-chain roots (highest value)

- Missing: `ROOT-062`, `ROOT-063`, `ROOT-064`, `ROOT-065`, `ROOT-066`,
  `ROOT-067`, `S102-A..D` entries in `root_registry.json`; regeneration of the
  canonical projection `canonical/root_cause_registry.json` (492 vs 530).
- Source: diffs/run tables already published in #355/#356 comments.
- Affected rows: FR-349..352, FR-355, FR-356, FR-NI-007.

## M2. In-repo Telegram journey document

- Missing: `docs/TELEGRAM_JOURNEY_S117_S119.md` (or English version) — the
  published copy lived on a preview host that is now dead.
- Source: #355/#356 comment text (preserved) + the session worklog.
- Affected rows: FR-NI-006 (UNVERIFIED_CLAIM).

## M3. Head re-execution of the Telegram protocol

- Missing: fresh `scripts/s117_tg_run.sh official|forkgram` runs at current
  HEAD (the S117 anchors were recorded on a different sandbox; the 5 store
  goldens re-verified this campaign do not cover Telegram).
- Affected rows: FR-016, FR-355, FR-356, FR-NI-003-G*.

## M4. Official-Telegram resource inventory (G18/G19)

- Missing: the committed official-APK inventory file referenced by G18; the
  G19 login-path resource enumeration is unchecked by design.
- Affected rows: FR-NI-003-G18, roadmap G19/G20.

## M5. Real-APK fan-out for micro-gap tickets

- Missing: per-ticket real-APK demonstrations for the 311 registry tickets
  (currently battery/gate-class, E2).
- Affected rows: FR-233 parent + FR-234..333.

## M6. Corpus executions for 161 NOT_TESTED titles

- Missing: runs + records for the 96 registry-orphan titles and 65
  title-registry NOT_TESTED rows with an issue record; or honest closure.
- Affected rows: FR-024..226 (PENDING block).

## M7. `.agent` law-file refresh

- Missing: updated `.agent/state.md` (still EXP-090) and
  `.agent/master_campaign_state.md` (still D05 era) — or an explicit pointer
  declaring CAMPAIGN_STATE.md as the single live state file.
- Affected rows: FR-NI-007 note; forensic evidence index records them STALE.

## M8. Repository-hygiene follow-through (evidence-preserving)

- Missing: removal/untracking decision for still-tracked disposable blobs —
  `tmp/archidx.json` (88.4 MB), `tmp/index-v1.json` (60.2 MB),
  `tmp/idx.jar` (14 MB), `run/exp077/*/view_tree.json` (22.4 + 21.8 MB).
  History rewrite NOT performed (law: no destructive rewriting without
  explicit justification).
- Affected rows: FR-NI-004.

## M9. Safir / Black sentinel APKs

- Missing: the APKs themselves — zero project records exist
  (BLOCKED-BY-IDENTITY, recorded honestly in CAMPAIGN_STATE).
- Affected rows: FINAL_COMPATIBILITY_CAMPAIGN checklist row 10.

## M10. Six reproduction scripts 1:1 cross-check

- Missing: file-by-file verification that the six scripts quoted in #361 exist
  in `scripts/` under the same names; issue-body copies are canonical until
  then.
- Affected rows: FR-361 (U7).
