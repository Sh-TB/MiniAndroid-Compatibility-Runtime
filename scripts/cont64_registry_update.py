#!/usr/bin/env python3
"""cont64_registry_update.py — CONT-64 W1 registry update: F-NEW-267 decode
deepens (stays ROOT-CAUSED-PARTIAL, honest). Appends the CONT-64 decode
section to the title and updates the last-verified fields."""
import json, re

PATH = "/home/z/my-project/root_registry.json"
with open(PATH) as f:
    reg = json.load(f)

for root in reg["roots"]:
    if root.get("id") == "F-NEW-267":
        old = root["title"]
        add = (" CONT-64 W1 DECODE (engine a00f331a-era, dooz v23): the EMPTY "
               "filter list root-caused to the zeroed Placeable.position "
               "store — the pure-DEX hit-test (Lc61; walk) reads Ld61;.i "
               "(Placeable.position packed IntOffset) which answers 0 for "
               "every walked node. Evidence chain: LN-DUMP probe (45+ "
               "Lel0; LayoutNodes live, parent chain q intact, coordinator "
               "Lkz0; per node); FIELD-TRACE Ld61;.i (410 puts: 359 zero + "
               "51 real screen positions incl. (960,0) settings-box and "
               "(729,498)/(771,540)/(0,540) top-region nodes; 154 gets ALL "
               "0 — the hit-test never reads a nonzero position); the "
               "place-then-reset pattern (i0() writes real position then 0 "
               "in the same batch) = a SECOND composition-time measure pass "
               "with broken constraints runs AFTER the real one and wins; "
               "CMT probe: Lt4;.onMeasure receives CORRECT EXACTLY|1080/"
               "EXACTLY|1920 specs (Lr;.i traversal) and calls s(root-"
               "constraints)+m(measureAndLayout) — but nothing is pending "
               "anymore so the real constraints never re-measure the tree; "
               "MainActivity.onCreate-frame AT_MOST|1080/1920 measures "
               "(R8-inlined compose setup) run LAST = last-measure-wins "
               "over the window state. Named missing law: the AOSP "
               "first-traversal ordering (a composition-time eager measure "
               "must not consume uninitialized root constraints — AOSP "
               "defers measure to the traversal). Fix lever (next wave): "
               "defer/eliminate the composition-time zero-measure or seed "
               "the delegate root constraints before the eager relayout "
               "consumes them; probes committed: MINIANDROID_LAYOUTNODE_DUMP, "
               "MINIANDROID_TOUCH_FIELD_TRACE, MINIANDROID_COMPOSE_MEASURE_"
               "TRACE, TOUCHWIN-ANSWER.")
        root["title"] = old + " " + add
        root["last_updated"] = "CONT-64 W1"
        reg["total_roots"] = len(reg["roots"])
        print("updated F-NEW-267; total roots:", len(reg["roots"]))
        break
else:
    raise SystemExit("F-NEW-267 not found")

with open(PATH, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print("registry written")
