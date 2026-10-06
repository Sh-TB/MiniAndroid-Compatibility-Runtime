#!/usr/bin/env python3
"""CONT-9 W5 — Phase 2 bounded-semantic-trace analyzer for F-NEW-256.

Parses [METHOD-IN] stderr traces and answers: WHO triggers the change-list
apply while the content composable is still executing?

Inputs: raw method-entry trace file (one [METHOD-IN] per line).
Outputs: compact structured events (stage/method/identity/caller-chain) per
the CONT-9 directive Phase 2 field contract.
"""
import re
import sys
from collections import Counter

# R8 class map (evidence/cont8/fnew256_w4_trace.json, dooz_23):
# Lnb0;=ComposerImpl  Lwo;=CompositionImpl  Lv02;=UiApplier  Ly11;=Change
# Lel0;=LayoutNode    Lon1;=SlotTable      Lrr0;=root content lambda
# Ld;=game-screen composable  Lom;=ComposableLambda  Lt4;=AndroidComposeView
STAGE = {
    "Lnb0;": "COMPOSER",
    "Lwo;": "COMPOSITION",
    "Lv02;": "UI_APPLIER",
    "Ly11;": "CHANGE_RECORD",
    "Lel0;": "LAYOUT_NODE",
    "Lon1;": "SLOT_TABLE",
    "Lrr0;": "ROOT_LAMBDA",
    "Lom;": "COMPOSABLE_LAMBDA",
    "Lt4;": "ANDROID_COMPOSE_VIEW",
}

ENTRY = re.compile(r"^\[(METHOD-IN)\] (L[^. ]*;)\.([^ ]+)")


def main(path):
    events = []          # (lineno, cls, method)
    with open(path, "r", errors="replace") as f:
        for i, line in enumerate(f):
            m = ENTRY.match(line)
            if m:
                events.append((i + 1, m.group(2), m.group(3)))

    print(f"total method entries: {len(events)}")

    # Decisive counts
    counts = Counter()
    spans = {}
    stack = []
    for lineno, cls, meth in events:
        counts[f"{cls}.{meth}"] += 1
        key = f"{cls}.{meth}"
        if key == "Ld;.i":
            if "Ld;.i" not in spans:
                spans["Ld;.i"] = [lineno, lineno]
            else:
                spans["Ld;.i"][1] = lineno
    for cls in STAGE:
        tot = sum(v for k, v in counts.items() if k.startswith(cls))
        print(f"  {STAGE[cls]:22s} {cls:8s} entries={tot}")
    if "Ld;.i" in spans:
        print(f"  Ld;.i span: {spans['Ld;.i'][0]} .. {spans['Ld;.i'][1]}")

    # First apply: first Lv02;.c entry (insertBottomUp == apply marker)
    apply_idx = next(
        (n for n, (ln, cls, mth) in enumerate(events) if cls == "Lv02;" and mth == "c"),
        None,
    )
    if apply_idx is None:
        print("NO APPLY FOUND (no Lv02;.c)")
        return

    aln = events[apply_idx][0]
    print(f"\nFIRST APPLY at trace-line {aln} (event #{apply_idx})")
    # Print the method-entry window BEFORE the apply — the bridge is here.
    lo = max(0, apply_idx - 45)
    print("\n--- 45 method entries before first apply ---")
    for ln, cls, mth in events[lo:apply_idx + 1]:
        stage = STAGE.get(cls, "")
        print(f"  L{ln:<7d} {cls}.{meth:24s} {stage}")

    # All change-record executions with index positions
    chg = [(n, ln) for n, (ln, cls, mth) in enumerate(events)
           if cls == "Ly11;" and mth == "a"]
    print(f"\nchange-record executions (Ly11;.a): {len(chg)}")
    for n, ln in chg[:12]:
        print(f"  event#{n} trace-line {ln}")

    # Last ROOT_LAMBDA / game-screen activity before/after apply
    after = events[apply_idx:apply_idx + 120]
    print("\n--- 40 entries AFTER first apply ---")
    for ln, cls, mth in after[:40]:
        print(f"  L{ln:<7d} {cls}.{meth}" if False else
              f"  L{ln:<7d} {cls}.{mth}")


if __name__ == "__main__":
    main(sys.argv[1])
