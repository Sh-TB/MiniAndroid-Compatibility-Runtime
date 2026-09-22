#!/usr/bin/env python3
"""s82_validator.py — S82 §44/§53: fail the run on any status without evidence.

Checks (each = a §44 rule):
  STATE_CHANGED   -> before/after SHAs + pixel diff
  RENDERED+       -> screenshot + SHA
  EXECUTED        -> session id + APK SHA + commit
  APK_READY       -> SHA present
  VISUAL_CORRELATED -> reference OK + comparison recorded
  VISUALLY_VERIFIED -> human review (never auto — any auto grant = FAIL)
  FIXED/RESOLUTION-> regression fields
  ISSUE_CLOSED    -> not checked here (no title issues closed this wave)
Also: evidence JPGs <=100KB, registry<->GitHub issue linkage counts.
Exit code 0 = all pass; nonzero = listing of violations.
"""
import glob
import json
import os
import sys

import s82_lib as L

fails = []


def check(cond, tid, rule):
    if not cond:
        fails.append(f"{tid}: {rule}")


def main():
    reg = L.load_registry()
    for t in reg["TITLES"]:
        tid = t["TITLE_ID"]
        ex = t.get("EXECUTION", "NOT_TESTED")
        state = t.get("STATE", "STATE-NOT-LOADED")
        if ex == "EXECUTED":
            check(bool(t.get("SESSION_ID")), tid, "EXECUTED && no session")
            check(bool(t.get("APK_SHA256")), tid, "EXECUTED && no APK SHA")
            check(bool(t.get("LAST_TESTED_COMMIT")), tid, "EXECUTED && no commit")
            check(state != "STATE-NOT-LOADED", tid, "EXECUTED && state NOT-LOADED")
        if state in ("STATE-RENDERED", "STATE-GRAPHICALLY-NONTRIVIAL",
                     "STATE-INTERACTIVE", "STATE-STATE-CHANGED",
                     "STATE-SEMANTICALLY-CORRELATED"):
            check(bool(t.get("SCREENSHOT_SHA256")), tid, "RENDERED && no screenshot SHA")
            check(bool(t.get("VISUAL")), tid, "RENDERED && no visual metrics")
        if t.get("STATE_CHANGE") == "PIXEL_DIFF_PROVEN":
            check(bool(t.get("BEFORE_FRAME_SHA256")) and bool(t.get("AFTER_FRAME_SHA256")),
                  tid, "STATE_CHANGED && no before/after")
            check((t.get("PIXEL_DIFF_PX") or 0) > 250, tid, "STATE_CHANGED && no diff>250")
        if t.get("VISUAL_CORRELATION") not in (None, "NONE", "NOT_REVIEWED"):
            check((t.get("REFERENCE") or {}).get("STATUS") == "OK", tid,
                  "VISUAL_CORRELATED && no reference")
            check(bool(t.get("COMPARISON")), tid, "VISUAL_CORRELATED && no comparison")
        check(t.get("HUMAN_VERIFICATION") != "VERIFIED" and state != "STATE-VISUALLY-VERIFIED",
              tid, "auto-L5 grant detected (forbidden §31)")
        if t.get("RESOLUTION") in ("FIXED", "VERIFIED"):
            check(bool(t.get("PREV_STATUS")) and t.get("STATE") != "STATE-NOT-LOADED",
                  tid, "FIXED/VERIFIED && no regression record")
        if str(ex).startswith("BLOCKED"):
            check(state == "STATE-NOT-LOADED", tid, "BLOCKED && state inflated")
    # evidence sizes
    for f in glob.glob(f"{L.EVID}/*.jpg"):
        sz = os.path.getsize(f)
        if sz > 102400:
            fails.append(f"EVIDENCE: {os.path.basename(f)} = {sz}B > 100KB")
    # linkage
    with_issue = sum(1 for t in reg["TITLES"] if t.get("ISSUE_NUMBER"))
    print(f"titles with linked issues: {with_issue}/{len(reg['TITLES'])}")
    print(f"evidence JPGs: {len(glob.glob(L.EVID + '/*.jpg'))}")
    if fails:
        print(f"VALIDATOR FAIL ({len(fails)}):")
        for f in fails[:50]:
            print("  -", f)
        sys.exit(1)
    print("VALIDATOR PASS — all §44 evidence gates hold")


if __name__ == "__main__":
    main()
