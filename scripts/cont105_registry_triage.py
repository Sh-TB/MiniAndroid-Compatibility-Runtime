#!/usr/bin/env python3
"""cont105_registry_triage.py — CONT-105 ×5 batch wave: per-root terminal
verdicts for the PARTIAL + UNPROVEN pools, evidence-based.

Verdict vocabulary (9-value law):
  CONFIRMED_OPEN_GAP / PARTIALLY_CONFIRMED / ALREADY_FIXED_AND_TESTED /
  ALREADY_TRACKED_OR_DUPLICATE / STALE_OR_SUPERSEDED / SOURCE_LEVEL_CANDIDATE_ONLY /
  NOT_APPLICABLE / REJECTED_WITH_REASON / BLOCKED_NEEDS_EVIDENCE

Rules (honest):
- verified_current==true  -> hold current status (VERIFIED row), no inflation.
- status PARTIAL/UNPROVEN + a LATER root-cause-fixed root covers the same
  face (title token overlap >= 2 content words, later date, FIXED status)
  -> STALE_OR_SUPERSEDED (by that root id).
- UNPROVEN + no evidence pointer -> BLOCKED_NEEDS_EVIDENCE (fixture-first law).
- UNPROVEN + evidence exists -> PARTIALLY_CONFIRMED (keep open, honest).
- PARTIAL + verified_current false + old date + fixed-family overlap -> superseded;
  otherwise PARTIALLY_CONFIRMED (stays open).
Outputs evidence/cont105/triage.json + a markdown table.
"""
import json, re, sys
from collections import Counter, defaultdict

REG = "root_registry.json"
OUT_JSON = "evidence/cont105/triage.json"
OUT_MD = "evidence/cont105/triage.md"

d = json.load(open(REG))
roots = d if isinstance(d, list) else d.get("roots", [])
by_id = {r["id"]: r for r in roots}

STOP = {"the", "a", "of", "in", "on", "for", "and", "or", "to", "via", "with",
        "at", "by", "from", "into", "under", "over", "law", "face", "family",
        "gap", "root", "fix", "path", "case", "test", "probe", "missing",
        "non", "silent", "false", "null", "dead", "generic", "new", "old",
        "live", "had", "was", "were", "been", "its", "this", "that", "one",
        "two", "three", "none", "every", "ever", "against", "copy"}


def toks(s):
    return {w for w in re.findall(r"[a-z][a-z0-9_]+", (s or "").lower()) if len(w) > 3 and w not in STOP and not re.fullmatch(r"r?new_?\d*", w)}


def overlaps(a, b):
    ta, tb = toks(a), toks(b)
    return len(ta & tb)


FIXED_SET = {"ROOT-CAUSED-FIXED", "ROOT_CAUSED_FIXED", "VERIFIED-FIXED",
             "ALREADY_FIXED_AND_TESTED", "IMPLEMENTED+TESTED"}

triage = []
for r in roots:
    st = r.get("status", "")
    if st not in ("PARTIAL", "UNPROVEN"):
        continue
    rid, title, date = r["id"], r.get("title", ""), r.get("date", "")
    vc = r.get("verified_current")
    ev = r.get("evidence", "")
    my_toks = toks(title)
    # find later fixed roots sharing content tokens. Guard against generic
    # short titles (e.g. "no live trace"): require >=3 tokens on BOTH sides
    # and overlap >= 50% of the smaller side — else the match is noise.
    sup = None
    best = 0
    for o in roots:
        if o["id"] == rid or o.get("status") not in FIXED_SET:
            continue
        if str(o.get("date", "")) <= str(date):
            continue
        ot = toks(o.get("title", ""))
        if len(my_toks) < 3 or len(ot) < 3:
            continue
        ov = len(my_toks & ot)
        if ov >= 2 and ov * 2 >= min(len(my_toks), len(ot)) and ov > best:
            best, sup = ov, o
    if vc is True:
        verdict, note = "HOLD-VERIFIED", f"verified_current=true at HEAD"
    elif sup is not None:
        verdict = "STALE_OR_SUPERSEDED"
        note = f"face covered by {sup['id']} ({sup.get('status')}, {sup.get('date')}); {best} content tokens overlap"
    elif st == "UNPROVEN":
        if ev:
            verdict, note = "PARTIALLY_CONFIRMED", "has evidence pointer; re-proof fixture-first pending"
        else:
            verdict, note = "BLOCKED_NEEDS_EVIDENCE", "no evidence pointer; fixture-first law gates any work"
    else:  # PARTIAL, not superseded
        verdict, note = "PARTIALLY_CONFIRMED", "residual honestly open; needs scoped re-proof"
    triage.append({"id": rid, "status": st, "vc": vc, "date": date,
                   "verdict": verdict, "note": note,
                   "superseded_by": sup["id"] if sup else None})

cnt = Counter(t["verdict"] for t in triage)
out = {
    "wave": "CONT-105",
    "registry_total": len(roots),
    "pools": {"PARTIAL": sum(1 for r in roots if r.get("status") == "PARTIAL"),
              "UNPROVEN": sum(1 for r in roots if r.get("status") == "UNPROVEN")},
    "triaged": len(triage),
    "verdict_counts": dict(cnt),
    "rows": triage,
}
import os
os.makedirs("evidence/cont105", exist_ok=True)
json.dump(out, open(OUT_JSON, "w"), indent=1)

with open(OUT_MD, "w") as f:
    f.write(f"# CONT-105 registry triage — {len(triage)} rows (PARTIAL+UNPROVEN pools)\n\n")
    f.write(f"pool sizes: {out['pools']} · verdicts: {dict(cnt)}\n\n")
    f.write("| id | status | vc | date | verdict | note |\n|---|---|---|---|---|---|\n")
    for t in triage:
        f.write(f"| {t['id']} | {t['status']} | {t['vc']} | {t['date']} | {t['verdict']} | {t['note'][:90]} |\n")

print("triaged:", len(triage), dict(cnt))
# registry integrity
ids = [r["id"] for r in roots]
dup = [i for i, c in Counter(ids).items() if c > 1]
print("id-unique:", not dup, "dups:", dup[:5])
