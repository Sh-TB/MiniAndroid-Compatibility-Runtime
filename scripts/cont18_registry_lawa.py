#!/usr/bin/env python3
"""CONT-18: update registry F-NEW-264d with LAW-A (parallel-store coherence)
implementation evidence. No status flips beyond evidence; umbrella row stays
REGISTERED until all six laws resolve (partial completion stays visible).
"""
import hashlib, json, subprocess, sys

BASE = "/home/z/my-project"
REG = f"{BASE}/root_registry.json"
HEAD = subprocess.run(["git", "-C", BASE, "rev-parse", "--short=8", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
BIN = hashlib.sha256(open(f"{BASE}/miniandroid/build/miniandroid",
                          "rb").read()).hexdigest()[:16]
TODAY = "2026-10-08"

reg = json.load(open(REG))
row = next((r for r in reg["roots"] if r.get("id") == "F-NEW-264d"), None)
if row is None:
    sys.exit("F-NEW-264d row not found")

law_a = (
    f"[CONT-18 LAW-A {TODAY}] PARALLEL-STORE COHERENCE LAW implemented+tested "
    f"at {BIN} (head {HEAD}): the four element stores "
    "(elements/elem_kinds/elem_strings/elem_ints) model ONE OpenJDK backing "
    "array; writers (add/insert/set/remove) now move all four in lockstep, "
    "readers resolve kind-aware. Faces: (1) remove(int) shared "
    "kind-faithful helper lawa_remove_index — the deque-family early "
    "intercept erased only elements -> stale get after remove (fcol K1 "
    "g2=false, traces run/cont18/k1trace + k1trace3); (2) contains "
    "kind-aware slot compare (kind-2 strings / kind-3 ints; fcol K9 flip); "
    "(3) NEW indexOf/lastIndexOf real handler (was generic-stub; OpenJDK "
    "first/last o.equals(elementData[i]) law, heap-array fallback "
    "layering); (4) F-NEW-238-SET diag false-positive for legal STRING "
    "writes fixed. fcol 3/18 -> 5/18 (K1+K9 PASS; K7/K8/K10 unchanged). "
    "Zero drift: anchors 6/6 x3 byte-identical at 57a2612db3a70d39; f266 "
    "6/6; f259 7/7; f259g 12/13 honest; negatives 19/19; skill 13/13. "
    "Real-APK exercise: opencalc ArrayList.remove x19 + dooz x9 via the "
    "shadow channel (method_trace REAL_DALVIK_INTERPRETER), byte-identical "
    "x3 — behavior-preserving on coherent stores. LAW-B..F remain PENDING "
    "(see evidence/cont18/CONT18_COLLECTION_AUDIT.md)."
)
prev = row.get("evidence", "")
row["evidence"] = (prev + " " + law_a).strip() if prev else law_a
row["date"] = TODAY
reg["note"] = reg.get("note", "")

json.dump(reg, open(REG, "w"), indent=2, ensure_ascii=False)
print("registry updated: F-NEW-264d evidence += LAW-A;", len(law_a), "chars")
print("status row:", row["status"], "| total:", reg.get("total"))
