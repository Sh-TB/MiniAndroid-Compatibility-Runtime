# MINIANDROID TICKET GUIDE

> **Canonical for ticket semantics** (S95-CTRL, 2026-09-25). Machine state:
> [TICKET_REGISTRY.json](TICKET_REGISTRY.json). Contributor routing:
> [MINIANDROID_CONTRIBUTING.md](MINIANDROID_CONTRIBUTING.md).

## What a ticket IS (and is not)

A ticket = **"this semantic area must be verified (or is proven broken)"** —
it does NOT automatically mean MiniAndroid is broken. A ticket with status
`UNTESTED`/`UNKNOWN` is a smallest-test request, not a bug report.

## Where each kind of truth lives (single source of truth law)

| Question | Canonical place |
|---|---|
| What did title X prove? | [ACHIEVEMENTS.md](ACHIEVEMENTS.md) + [evidence/canonical/registry.json](evidence/canonical/registry.json) |
| Why did the engine fail at root R? | [root_registry.json](../root_registry.json) (append-only) |
| What problems are open and their state? | [TICKET_REGISTRY.json](TICKET_REGISTRY.json) |
| What is next in order? | [MINIANDROID_MASTER_QUEUE.md](MINIANDROID_MASTER_QUEUE.md) |
| Which upstream source do I reuse? | [GRAPHICS_SOURCE_REGISTRY.md](GRAPHICS_SOURCE_REGISTRY.md) (+ `tools/source_lookup.py <category>`) |
| Strategic 0→100 layers? | [MINIANDROID_0_TO_100.md](MINIANDROID_0_TO_100.md) |

Historical systems that remain valid but are now VIEWs (do not double-edit):
`docs/audit/RUNTIME_FAILURE_REGISTRY.md` (generated from root_registry),
`docs/audit/CRASH_HANG_ANR_REGISTRY.md`, `docs/development/STUB_DEBT.md`,
`docs/maintenance/CLOSURE_QUEUE.md`, `docs/maintenance/NOT_DONE.md`.
Title-level parent records: ACHIEVEMENTS.md IS the app/game master record
system (one record per title, S84 law); APP-xxxx/GAME-xxxx tickets exist only
where a failure family needs a problem-state parent.

## Ticket identifiers

Stable, never reused: `GFX-###` graphics · `TEXT-###` text · `AUDIO-###` ·
`VIDEO-###` · `MEDIA-###` · `NET-###` network · `WEB-###` web/webview ·
`DEX-###` dex/runtime · `CONC-###` concurrency · `STORE-###` storage ·
`JNI-###` native · `COMPOSE-###` · `LAYOUT-###` · `API-###` ·
`APP-####` app master record · `GAME-####` game master record.

## Status vocabulary (exact)

`UNKNOWN` · `UNTESTED` · `OBSERVED` · `PARTIAL` · `FAILED` ·
`ROOT_CAUSE_FOUND` · `IMPLEMENTED` · `TESTED` · `VERIFIED` · `BLOCKED` ·
`PENDING` · `CLOSED` · `SUPERSEDED`

Lifecycle: `UNKNOWN/UNTESTED → OBSERVED (real APK) → ROOT_CAUSE_FOUND →
IMPLEMENTED → TESTED → VERIFIED → CLOSED` (or `SUPERSEDED` with a pointer).
Evidence must rise E0→E6 with each step:
E0 hypothesis · E1 source · E2 unit · E3 runtime trace · E4 real APK ·
E5 deterministic repeated APK · E6 corpus fan-out.

**A capability cannot be marked DONE without the appropriate evidence level.
"Implemented" ≠ "verified."**

## Ticket format (full field list — mirrored in JSON)

Every ticket carries: Identity (id, subsystem, capability, priority,
status, created, last_verified_commit) · Why It Matters · Semantic Contract
(what Android should do) · Current MiniAndroid Behavior · First Divergence ·
Root Cause (only when proven; otherwise `NOT_PROVEN`) · Upstream Sources
(repo/pinned-SHA/file/symbol/test) · Reuse Strategy (`DIRECT_REUSE, ADAPT,
PORT_ALGORITHM, PORT_TEST, PORT_FIXTURE, REFERENCE_ONLY`) · Implementation
Plan (smallest semantic change) · Test Plan (unit/fixture/integration/APK/
control/regression) · Corpus Fan-Out (potential/executed/improved) ·
Definition of Done · Contributor Help.

## How to take a ticket (the 9-step §170 chain)

1. `python3 tools/source_lookup.py <category>` — automatic upstream map.
2. Open the ticket's `upstream_sources` (pinned SHAs) — read source AND tests.
3. Restate the semantic law in one sentence; get it into the ticket.
4. Build/borrow the smallest fixture (PORT_FIXTURE first).
5. Implement the smallest semantic change (ADAPT > PORT_ALGORITHM > custom;
   justify any custom code in the ticket).
6. Add the regression stage to the battery (zero-skip law).
7. Re-execute ≥2 target APKs + ≥2 control APKs, same protocol; record
   before/after hashes and metrics.
8. Update the ticket (status + evidence links) and ROI fields.
9. Run `python3 tools/validate_control_system.py` — the consistency gate.

## Anti-false-claim rules (S92/S93, always in force)

No FULLY_VERIFIED from: nonblank image, entropy, color count, PNG validity,
process exit 0, PIL opening. Screenshots need semantic evidence. Frozen-
animation claims need ≥3 deterministic runs proving state A ≠ state B. A
threshold may never be tuned to make a failing case pass (GFX-005 is the
example: fix truth, not the floor).

## Machine validation

`python3 tools/validate_control_system.py` checks: unique ticket IDs, status
vocabulary, README↔registry↔matrix↔queue↔register number consistency, link
existence. CI-style usage: run before every commit that touches docs.
