#!/usr/bin/env python3
"""s75_registry_update.py — S75 CLOSURE WAVE registry + doc updates.

Updates (evidence-locked, no invented semantics):
1. root_registry.json A7: ROOT-CAUSED-NOT-FIXED -> FIXED-S75 (label/icon
   resid capture + ARSC resolve implemented + f54 fixture proof) with the
   S75 evidence string appended to the existing evidence (append-only).
2. root_registry.json F-146/F-147: append the S75 HEAD re-probe evidence
   (both escapes reproduced at HEAD + F-147 p0=NULL register observation).
3. summary.last_updated -> S75.
Statuses follow the registry's own vocabulary; evidence is appended, never
rewritten (single-source-of-truth + honesty laws).
"""
import json
from datetime import datetime, timezone

ROOT = "/home/z/my-project"
P = f"{ROOT}/root_registry.json"

d = json.load(open(P))
A7_EVIDENCE = (" | S75 CLOSURE: FIXED — ManifestReader captures "
    "application_label_resid/application_icon_resid for REFERENCE-typed attrs "
    "(manifest_reader.cpp A7 block; literal '@0x' degrade removed) + "
    "ManifestReader::resolve_resid_string (ARSC resolve, nullopt on miss, "
    "never invented) wired at the ResourceRuntime ensure_loaded site "
    "(execution_engine.cpp, AOSP PackageParser labelRes/loadLabel law); "
    "f54_manifestlabel fixture: label REFERENCE @string/app_name resolved "
    "to 'F54 LabelProof' ([A7] engine.log line) + icon resid @0x7f010000 "
    "captured; verifier f54 6/6 asserts, 24/24 total PASS; battery 26/26 "
    "rc=0 on the A7 binary; Level C snake replay byte-identical 90/90 "
    "(render-neutral proof). Status vocabulary: ROOT-CAUSED-NOT-FIXED -> "
    "FIXED-S75 (fixture-tested).")
F146_EVIDENCE = (" | S75 HEAD re-probe (docs/evidence/s75/dooz_f146_probe/): "
    "escape reproduced at HEAD c67230be (MINIANDROID_F141_DIAG=1) — same "
    "g8.a pc=569 site, receiver v4:t8/o0 (NULL_REF), invoked "
    "Ljava/lang/Object;.getClass; NEW OBSERVATION (recorded, not claimed as "
    "law): the SECONDARY F-147 site fires with p0 (frame this-register) "
    "itself t8/o0 NULL — consistent with F-147 being downstream of the "
    "F-146 coroutine unwind; black region 23,472 px bbox (0,0)-(488,47) "
    "byte-consistent with the reclassified engine-default face; ViewTree "
    "= App + 2 View + Lg10 + 2 Loc1 (Compose chain, no game content).")
F147_EVIDENCE = (" | S75 HEAD re-probe: reproduced at HEAD "
    "(MainActivity.onCreate pc=228, recv p0:t8/o0 NULL) — see F-146 entry "
    "for the shared probe; secondary-to-F-146 reading recorded as an "
    "OBSERVATION, upstream producer trace still OPEN.")

found = {"A7": False, "F-146": False, "F-147": False}
for r in d.get("roots", []):
    rid = str(r.get("id"))
    if rid == "A7":
        r["status"] = "FIXED-S75"
        r["evidence"] = r.get("evidence", "") + A7_EVIDENCE
        found["A7"] = True
    elif rid == "F-146":
        r["evidence"] = r.get("evidence", "") + F146_EVIDENCE
        found["F-146"] = True
    elif rid == "F-147":
        r["evidence"] = r.get("evidence", "") + F147_EVIDENCE
        found["F-147"] = True

assert all(found.values()), f"missing roots: {[k for k,v in found.items() if not v]}"

d.setdefault("summary", {})["last_updated"] = \
    f"S75 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
n = len(d.get("roots", []))
d["summary"]["total_roots"] = n  # roots count unchanged (A7/F-146/F-147 already registered)

with open(P, "w") as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print(f"registry updated: A7 -> FIXED-S75; F-146/F-147 evidence appended; roots={n}")
