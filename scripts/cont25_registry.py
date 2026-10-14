#!/usr/bin/env python3
"""cont25_registry.py — CONT-25 / PHASE 1 registry update.

Root accounting (directive §15): NO new roots.
- F-NEW-277 (CLASSIFIED P0): evidence extended with the CONT-25 decode —
  the pump quiescence arm of the fix surface LANDED (poll-timeout parity,
  patch binary e980887e); the divergence moved to the invalidation-delivery
  link; the 'slot tracking' wording from the external probe is corrected:
  the Composer/slot machinery is healthy, composition #2 never starts.
- R-NEW-331 (PARTIAL): itsfrz tictactoe face attached (FragmentContainerView
  fm=null NPE, pre-Composer, Compose corpus control B).
- R-NEW-345 (IMPLEMENTED): droidify residual arm attached (DelayKt.runBlocking
  HALT-LOOP at the joinBlocking park loop, pre-Composer, Compose corpus
  control C).
"""
import json

PATH = "/home/z/my-project/root_registry.json"
r = json.load(open(PATH))
roots = r["roots"]
by_id = {row.get("id"): row for row in roots}

CONT25 = ("CONT-25 pointer 2026-10-08: PHASE-1 compose-root test — pump-side "
          "arm of the fix surface LANDED: F-NEW-277 POLL-TIMEOUT PARITY in "
          "pump_compose_frames (scoped fired_frames>0; FINDING-009 law parity), "
          "patch binary e980887e39aee977, 18/18 anchors + probe battery green, "
          "flappycow/tictactoe byte-identical. [F277-POLL] fires on dooz (the "
          "16ms View.post strand now runs; was stranded/removed-never-run) but "
          "recomposition #2 STILL never runs — wake-up work is not in the "
          "handler queue (only 13 trampoline tasks dispatch in 15s). NEXT "
          "LINK: the invalidation-delivery chain (produceState/LaunchedEffect "
          "collect dispatch / StateFlow first-emit / GlobalSnapshotManager "
          "channel monitor). Corrected classification: NOT slot tracking — "
          "the Composer runs (Lrn1 x10366) and composition #1 is legal; "
          "scheduler-layer starvation. Evidence: evidence/cont25/"
          "COMPOSE_ROOT_TEST.md; runs run/cont25/*; trace run/cont25/probe_pump.")

row = by_id["F-NEW-277"]
assert row, "F-NEW-277 missing"
ev = row.get("evidence")
ev = ev if isinstance(ev, str) else json.dumps(ev, ensure_ascii=False)
row["evidence"] = ev + " " + CONT25
row["verified_current"] = (
    "patch binary e980887e39aee977 (CONT-25): [F277-POLL] poll-timeout "
    "fast-forward fires once on dooz (15s and 120s protocols, deterministic "
    "d602648e8e401895 x3); scope-guard proven — itsfrz/droidify runs inert "
    "(fired_frames=0); 18/18 anchors x3 byte-identical; fcol 20/20, f259 7/7, "
    "f259g 12/13 known-honest F259-L, f266 6/6, f268; flappycow 13cf4746 + "
    "tictactoe b5a7a35d byte-identical to baseline fa88902f. Composition "
    "progress: NO — next divergence recorded.")

# R-NEW-331: attach itsfrz face
row331 = by_id.get("R-NEW-331")
if row331:
    ev = row331.get("evidence")
    ev = ev if isinstance(ev, str) else json.dumps(ev, ensure_ascii=False)
    row331["evidence"] = ev + (
        " CONT-25 pointer 2026-10-08: NEW FACE — com.itsfrz.tictactoe 1.0.5 "
        "(vc5, Compose corpus control B, sha 2a057a9a519acd81): NPE "
        "'Parameter specified as non-null is null: method androidx.fragment."
        "app.FragmentContainerView.<init>, parameter fm' (caller Lo4/k;.e) "
        "unwinds to MainActivity.onCreate [APP-BOUNDARY] BEFORE any Compose "
        "entry — pre-Composer blocker, 3 uncaught, blank frame d55056a8 "
        "x3. Next action: supportFragmentManager/FragmentContainerView(fm) "
        "host law. Evidence: run/cont25/base_itsfrz; evidence/cont25/"
        "COMPOSE_ROOT_TEST.md §2.")

# R-NEW-345: attach droidify residual arm
row345 = by_id.get("R-NEW-345")
if row345:
    ev = row345.get("evidence")
    ev = ev if isinstance(ev, str) else json.dumps(ev, ensure_ascii=False)
    row345["evidence"] = ev + (
        " CONT-25 pointer 2026-10-08: RESIDUAL ARM — com.looker.droidify "
        "0.7.7 (vc770, Compose corpus control C, sha da3070f3f18bdbed): "
        "[HALT-LOOP] 50001 visits at PC=0x5a in kotlinx.coroutines.DelayKt."
        "runBlocking (joinBlocking park loop) -> F084 VirtualMachineError -> "
        "APP-BOUNDARY BEFORE any Compose entry (4 uncaught; protobuf Lite "
        "faces) — the R-NEW-345 park-drain law drains queued work but the "
        "joinBlocking coroutine never completes (isCompleted never observed "
        "true). Pre-Composer blocker, blank frame b5a7a35d x3. Next action: "
        "runBlocking event-loop pump law (BlockingEventLoop task queue). "
        "Evidence: run/cont25/base_droidify; evidence/cont25/"
        "COMPOSE_ROOT_TEST.md §2.")

json.dump(r, open(PATH, "w"), indent=1, ensure_ascii=False)
print("registry updated: total =", len(roots))
print("F-NEW-277 evidence extended:", "CONT-25 pointer" in row["evidence"])
print("R-NEW-331 evidence extended:", bool(row331) and "CONT-25 pointer" in row331["evidence"])
print("R-NEW-345 evidence extended:", bool(row345) and "CONT-25 pointer" in row345["evidence"])
