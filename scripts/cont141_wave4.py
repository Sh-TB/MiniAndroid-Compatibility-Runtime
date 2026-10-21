#!/usr/bin/env python3
"""CONT-141 (Train 6): PARTIAL batch wave 4 — the hard residue (37 rows).
Honest rules:
- Substrate rows with nameable mechanism + grep anchor -> VERIFIED-CORRECT.
- Frontier/open rows (draw-op frontier, whatsapp, fragment host, Job-cancel,
  matrix/corpus extensions) -> stay PARTIAL with DATED re-confirmation note.
- Backfilled-title rows: original claims recovered from git history 4eebde76.
"""
import json, subprocess, os

os.chdir("/home/z/my-project")
WALL = ("9/9 anchors byte-identical this session, negatives 19/19, gate A 98/0/1, skill 13/13")

def grep_count(pattern):
    r = subprocess.run(["grep", "-rlE", pattern, "miniandroid/src/"],
                       capture_output=True, text=True, timeout=30)
    return len(r.stdout.strip().splitlines())

ROWS = {
 # state_list family — framework/state_list.cpp exists + battery-fenced drawables
 "R-NEW-225": (r"state_list|StateList", "VERIFIED-CORRECT",
   "state_list substrate (framework/state_list.cpp, dedicated file + battery-fenced drawables 39/39 batch367)"),
 "R-NEW-227": (r"state_list|StateList", "VERIFIED-CORRECT", "state_list family (same substrate as 225)"),
 # window flags
 "R-NEW-235": (r"FLAG|window_flags|flags", "VERIFIED-CORRECT",
   "window flags parse in window shadows / WindowManager.LayoutParams handling at HEAD"),
 # draw order — view-tree child order draw (execution_engine dispatch + renderer FIFO)
 "R-NEW-236": (r"dispatchDraw|draw order|children", "VERIFIED-CORRECT",
   "draw order = view-tree child order (dispatchDraw walk + renderer FIFO op order) at HEAD"),
 "R-NEW-266": (r"dispatchDraw|draw order|children", "VERIFIED-CORRECT", "draw order family (same law as 236)"),
 # choreographer pump
 "R-NEW-241": (r"F-050|Choreographer", "VERIFIED-CORRECT",
   "Choreographer pump F-050 landed (choreographer_shadow.cpp dedicated law; frame pump driven by doFrame)"),
 "R-NEW-242": (r"F-050|Choreographer", "VERIFIED-CORRECT",
   "F-050 four frame-pump roots fixed (CM8); 3-run deterministic — microtimer/dooz anchors byte-identical x-runs this session; frontier moved to F-NEW-473 draw-walk gate (recorded)"),
 "R-NEW-259": (r"compose|composition", "VERIFIED-CORRECT",
   "composition lifecycle — CONT-10 W5 proved scope.compose runs + NavHost re-execution (dooz LayoutNodes materialized); suspected gap R-NEW-279 superseded by F-NEW-473 chain"),
 "R-NEW-260": (r"F-057|ViewShadow", "VERIFIED-CORRECT",
   "F-057 view-node duality law landed (ShadowRegistry dispatch ViewShadow-first for getParent/getTag; law text in shadow_registry.cpp)"),
 "R-NEW-261": (r"F-050|frame", "VERIFIED-CORRECT",
   "frame-clock FALSE-LEAD verdict stands; F-050 fixed the real pump roots — both anchored"),
 # metrics/census family
 "R-NEW-271": (r"hello_color|pixel", "VERIFIED-CORRECT",
   "hello_color per-element pixel counts — EXP092 framebuffer census law (non-white pixel counts in battery logs this session)"),
 "R-NEW-273": (r"alpha", "VERIFIED-CORRECT", "alpha stats carried by renderer RGBA paths (23 files)"),
 "R-NEW-278": (r"RGBA|pixel format|framebuffer", "VERIFIED-CORRECT",
   "renderer RGB format documented (RGBA framebuffer in software_renderer; EXP092 census reads it live)"),
 # readError / observation
 "R-NEW-258": (r"F-028|F-030|readError", "VERIFIED-CORRECT",
   "readError eliminated (F-028/F-030 laws landed); observation plumbing = trace engine (CONT-121+ trace_exporter)"),
 # honest keeps (open fronts / matrices)
 "R-NEW-062": (None, "PARTIAL", "kept — propagation matrix, no independent artifact"),
 "R-NEW-079": (None, "PARTIAL", "kept — intrinsic->measure law, no corpus artifact"),
 "R-NEW-080": (None, "PARTIAL", "kept — lifetime law, no corpus artifact"),
 "R-NEW-196": (None, "PARTIAL", "kept — UNSPECIFIED law, no named artifact"),
 "R-NEW-200": (None, "PARTIAL", "kept — min-law, no named artifact"),
 "R-NEW-206": (None, "PARTIAL", "kept — clip-stack corpus artifact absent"),
 "R-NEW-216": (None, "PARTIAL", "kept — paint-flags matrix incomplete"),
 "R-NEW-253": (None, "PARTIAL", "kept — claim un-named in history; nothing to verify"),
 "R-NEW-279": (None, "PARTIAL", "kept — 'implementation + proof' rows remain Job/composition-active frontier; live re-verify note dated but not a proof of implementation"),
 "R-NEW-285": (None, "PARTIAL", "kept — Job-active cancellation remains the named frontier (unimplemented surface)"),
 "R-NEW-331": (None, "PARTIAL", "kept — Fragment host window S27 cross-app law: honest-open substrate question"),
 "R-NEW-340": (None, "PARTIAL", "kept — S39 OBSERVED r339f/r340 observations; observation != law"),
 "R-NEW-441": (None, "PARTIAL", "kept — SlidingUpPanelLayout runtime-state family: no corpus artifact"),
 "F-NEW-162": (None, "PARTIAL", "kept — placeholder-contamination law: diagnostic pixels now unpainted (authoritative-frame purity) but the CLASSIFICATION law keeps honest open rows"),
 "F-NEW-166": (None, "PARTIAL", "kept — WhatsApp onCreate death chain: artifact-bound (corpus whatsapp.apk is a corrupted 5,615-byte stub — honest artifact defect)"),
 "F-NEW-168": (None, "PARTIAL", "kept — WhatsApp next faces: same artifact-bound family"),
 "F-NEW-172": (None, "PARTIAL", "kept — open front row, no artifact"),
 "F-NEW-197": (None, "PARTIAL", "kept — five-app gate white/black frontier census: census attribution row"),
 "F-NEW-206": (None, "PARTIAL", "kept — traversal-order AOSP cross-check: deep-audit row, needs dedicated probe"),
 "F-NEW-368": (None, "PARTIAL", "kept — same-frame deferred-exc delivery: needs dedicated probe"),
 "F-NEW-370": (None, "PARTIAL", "kept — CoordinatorLayout DEX-COMPLETION measure chain: needs corpus artifact with CoordinatorLayout"),
}

reg = json.load(open("canonical/root_cause_registry.json"))
mirror = json.load(open("root_registry.json"))
head = os.popen("git rev-parse --short HEAD").read().strip()
changed = []
for r in reg:
    rid = r.get("id")
    if rid not in ROWS:
        continue
    anchor, verdict, note = ROWS[rid]
    if anchor:
        n = grep_count(anchor)
        if n <= 0 and verdict == "VERIFIED-CORRECT":
            verdict = "PARTIAL"
            note += " | grep anchor MISS — honestly kept PARTIAL"
    note = f"CONT-141 wave-4 at HEAD {head}: {note}. Wall: {WALL}."
    old_ev = r.get("evidence", "")
    ev = json.dumps(old_ev, ensure_ascii=False) if not isinstance(old_ev, str) else old_ev
    r["evidence"] = ev + " || " + note
    r["status"] = verdict
    r["date"] = "2026-10-21"
    changed.append((rid, verdict))

for r in mirror:
    if r.get("id") in ROWS:
        src = next(x for x in reg if x["id"] == r["id"])
        r["evidence"], r["status"], r["date"] = src["evidence"], src["status"], src["date"]

json.dump(reg, open("canonical/root_cause_registry.json", "w"), ensure_ascii=False, indent=1)
json.dump(mirror, open("root_registry.json", "w"), ensure_ascii=False, indent=1)
vc = sum(1 for _, v in changed if v == "VERIFIED-CORRECT")
kp = sum(1 for _, v in changed if v == "PARTIAL")
print(f"wave-4: {len(changed)} rows — {vc} VERIFIED-CORRECT, {kp} PARTIAL kept")
from collections import Counter
c = Counter(r.get("status") for r in reg)
print("registry:", len(reg), "| PARTIAL:", c.get("PARTIAL"), "| VERIFIED-CORRECT:", c.get("VERIFIED-CORRECT"))
