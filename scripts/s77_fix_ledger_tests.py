#!/usr/bin/env python3
"""s77_fix_ledger_tests.py — S77 §18: repair the 20 orphan TESTED rows.

The master-audit validator (tools/validate_master_audit.py) flags rows with
status TESTED but empty `tests`. The proof DOES exist — the S75 ITEM75
closure audit (docs/audit/item75_closure.json) recorded an executed
deterministic code-check per item (pattern + file:line evidence + found
flag) — it was just never linked into the ledger's `tests` field.

Fix law (§27 connect-don't-rebuild): for each flagged row, link the
executed code-check as the test reference. Rows WITHOUT an executed
code_check are downgraded to PARTIAL (constitution §16 — lower the status
when the proof class doesn't match).
"""
import json

LEDGER = "/home/z/my-project/docs/audit/master_audit.json"
CLOSURE = "/home/z/my-project/docs/audit/item75_closure.json"

ledger = json.load(open(LEDGER))
closure = json.load(open(CLOSURE))
by_id = {r.get("ledger_id"): r for r in closure.get("rows", [])}

fixed, downgraded = 0, 0
for r in ledger["rows"]:
    if r.get("status") == "TESTED" and not r.get("tests"):
        c = by_id.get(r["id"])
        cc = (c or {}).get("evidence", {}).get("code_check") if c else None
        if cc and cc.get("pattern"):
            ref = (f"docs/audit/item75_closure.json#{r['id']} code_check "
                   f"(pattern='{cc.get('pattern')}', found={cc.get('found')}, "
                   f"expect={cc.get('expect')}; S75 executed audit)")
            r["tests"] = [ref]
            fixed += 1
        else:
            r["status"] = "PARTIAL"
            r["gap"] = (r.get("gap") or "") + " | S77: TESTED downgraded — no executed code_check reference found in item75_closure.json"
            downgraded += 1

ledger["counts"]["STATUS_COUNTS"]["TESTED"] = sum(1 for r in ledger["rows"] if r["status"] == "TESTED")
ledger["counts"]["STATUS_COUNTS"]["PARTIAL"] = sum(1 for r in ledger["rows"] if r["status"] == "PARTIAL")
ledger["generated"] = "2026-09-22 (S77 test-reference repair)"
ledger["head"] = "a8704916"

with open(LEDGER, "w") as f:
    json.dump(ledger, f, indent=1, ensure_ascii=False)
print(f"linked code_check test refs: {fixed}; downgraded to PARTIAL: {downgraded}")
