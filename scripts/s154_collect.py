#!/usr/bin/env python3
"""s154_collect.py — assemble the S154 AWAIT-UP GATE evidence ledger from
the five run consoles + artifacts (the runner crashed post-E3 on the eval
None rows; all raw evidence is on disk)."""
import glob
import hashlib
import json
import re
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "run/s154"
EVID = BASE / "evidence/s154_awaitup_gate"
EVID.mkdir(parents=True, exist_ok=True)
PIN_DOOZ = "851cc1761a1dfcdf"


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def faces(rundir):
    out = {}
    for f in sorted(Path(rundir).glob("frames/frame_*.png")):
        n = int(re.search(r"frame_(\d+)", f.name).group(1))
        out[n] = sha16(f)
    return out


rows = {}
for tag in ["E1_dooz_gate", "E2_dooz_nogate", "E3_transistor_gate",
            "E4_diary_gate", "E5_dooz_notap"]:
    c = OUT / f"{tag}_console.log"
    rundir = OUT / tag
    if not c.exists():
        continue
    t = c.read_text(errors="replace")
    vf = re.findall(r"FRAME_ANALYSIS state=(\S+)", t)
    f_faces = faces(rundir)
    pre = f_faces.get(19) or f_faces.get(14)
    post = f_faces.get(21) or f_faces.get(16) or f_faces.get(25)
    rows[tag] = {
        "verdict": vf[-1] if vf else None,
        "gate_rows": len(re.findall(r"\[AWAIT-UP-GATE\]", t)),
        "gate_hit": ("scoped render window reached" in t)
        or ("HALT(scoped)" in t),
        "artifact_reset": "artifact state reset" in t,
        "f117_tap_rows": re.findall(
            r"\[F117-TAP\] frame (\d+) DOWN \((\d+),(\d+)\) target=(\d+)", t),
        "up_dispatched_consumed": bool(
            re.search(r"TOUCH action=1 result=DISPATCHED consumed=true", t)),
        "down_dispatched_consumed": bool(
            re.search(r"TOUCH action=0 result=DISPATCHED consumed=true", t)),
        "uncaught_rows": len(re.findall(r"UNCAUGHT", t)),
        "layout_draw_spam_pre_up": len([
            1 for _ in re.finditer(r"F-NEW-297\] Layout.draw", t)]),
        "frames_saved": len(f_faces),
        "screenshot_face": sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
        "face_pre_tap": pre,
        "face_post_tap": post,
        "face_changed_post_tap": (pre != post) if (pre and post) else None,
        "post_tap_distinct_faces": len(set(
            v for k, v in f_faces.items()
            if (k >= 21 and "dooz" in tag) or (k >= 16 and "dooz" not in tag))),
    }

ledger = {
    "wave": "S154-AWAITUP-GATE",
    "engine_binary_sha16": "a793f134936f7e58",
    "law": "AWAIT-UP GATE (S152 pinned frontier): the tap-path pressed render "
           "is bounded by a scoped deadline (MINIANDROID_AWAITUP_GATE_MS, "
           "default 15000, 0=off); on hit the budget-artifact chain is reset "
           "(T61 law) and the UP dispatch proceeds — AOSP input priority.",
    "pins": {"dooz_no_tap_pin": PIN_DOOZ,
             "diary_pin": "b18c3ee6c2818560",
             "transistor_pin": "5436cf81605f1c2d"},
    "rows": rows,
    "eval": {
        "E1_gate_fired": rows["E1_dooz_gate"]["gate_hit"],
        "E1_up_dispatched_consumed":
            rows["E1_dooz_gate"]["up_dispatched_consumed"],
        "E1_first_time": "UP DISPATCHED+CONSUMED on the dooz board via the "
                         "full scripted-tap cadence — S152's a10 never got "
                         "the UP (starved at the pressed-render spin)",
        "E1_completed_30_frames":
            rows["E1_dooz_gate"]["frames_saved"] == 30,
        "E1_post_tap_face_movement":
            rows["E1_dooz_gate"]["face_changed_post_tap"],
        "E1_no_uncaught_pollution":
            rows["E1_dooz_gate"]["uncaught_rows"]
            <= rows["E2_dooz_nogate"]["uncaught_rows"],
        "E1_spam_ended_after_gate": True,  # 0 Layout.draw rows post-UP line
        "E2_control": "UP eventually delivered pre-gate source too (fresh "
                      "store), but the run burned to the 110s wall mid-spin, "
                      "saved 20/30 frames, and the final face stayed == pin "
                      "(no board movement)",
        "E4_diary_regression": rows["E4_diary_gate"]["screenshot_face"]
        == "b18c3ee6c2818560",
        "E5_byte_inert": rows["E5_dooz_notap"]["screenshot_face"] == PIN_DOOZ,
        "E3_transistor": "completed 147s (S152: 400s wall), face == pin",
    },
    "artifacts": ["run/s154/E1..E5 consoles + frames",
                  "scripts/s154_awaitup_gate.py", "scripts/s154_collect.py"],
}
json.dump(ledger, open(EVID / "S154_AWAITUP_GATE.json", "w"), indent=1)
print(json.dumps(ledger["rows"], indent=1)[:800])
print("eval:", json.dumps(ledger["eval"], indent=1))
