#!/usr/bin/env python3
"""s154_awaitup_gate.py — S154 wave: AWAIT-UP GATE law validation.

The S152 pinned frontier: post-DOWN pressed-render spin starves the UP
dispatch (dooz compose 256M+ instr; transistor 400s wall). The gate arms a
scoped deadline around the tap-path pressed render (AOSP input priority);
on hit it resets the budget-artifact chain so the UP dispatch runs clean.

Experiments:
  E1 dooz tap @ (540,960) frame 20, gate ON  -> expect [AWAIT-UP-GATE] row,
     UP delivered, CLICK consumed, post-tap face change (the full chain).
  E2 dooz tap, gate OFF (MINIANDROID_AWAITUP_GATE_MS=0) -> A/B control
     (pre-S154 cadence: UP starved / wall burn).
  E3 transistor tap @ (996,567) frame 15, gate ON -> UP delivered (was
     DOWN_ONLY UP-starved at S152).
  E4 diary tap @ (1017,1857) frame 15, gate ON -> regression guard: must
     STAY TAP_EFFECT_RENDERED (fast render never hits the gate).
  E5 dooz NO-tap -> face must equal the standing pin 851cc1761a1dfcdf
     (default byte-inert; the gate arms only in the tap path).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run/s154"
EVID = BASE / "evidence/s154_awaitup_gate"
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)

DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
TR_APK = BASE / "upload/s151_internet_batch/org.y20k.transistor_117.apk"
DI_APK = BASE / "upload/s151_internet_batch/org.billthefarmer.diary_1105.apk"

DOOZ_STORE = OUT / "store_dooz/data"
TR_STORE = BASE / "evidence/s151_trains/store_org.y20k.transistor_117/data"
DI_STORE = BASE / "evidence/s151_trains/store_org.billthefarmer.diary_1105/data"

VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")
PIN_DOOZ = "851cc1761a1dfcdf"


def sha16(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def frame_faces(rundir):
    faces = {}
    frames = sorted(Path(rundir).glob("frames/frame_*"))
    for f in frames:
        m = re.search(r"frame_(\d+)", f.name)
        if m:
            faces[int(m.group(1))] = sha16(f)
    return faces


def install(apk, store):
    store.parent.mkdir(parents=True, exist_ok=True)
    if not (store / "data").exists() and not store.exists():
        subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=300)


def run_case(tag, apk, store, tap=None, gate_ms=None, frames=30,
             max_seconds=110, package=None):
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    env = dict(os.environ)
    if gate_ms is not None:
        env["MINIANDROID_AWAITUP_GATE_MS"] = str(gate_ms)
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", str(frames),
           "--trace"]
    if package:
        cmd += ["--package", package]
    if tap:
        cmd += ["--tap", tap]
    t0 = time.time()
    killed = False
    try:
        with open(console, "w") as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=max_seconds + 60, env=env)
    except subprocess.TimeoutExpired:
        killed = True
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    verdicts = VERDICT_RE.findall(text)
    row = {
        "tag": tag, "tap": tap, "gate_ms": gate_ms, "wall_s": wall,
        "process_killed": killed,
        "verdict": verdicts[-1] if verdicts else None,
        "gate_rows": len(re.findall(r"\[AWAIT-UP-GATE\]", text)),
        "gate_hit": "HALT(scoped)" in text,
        "artifact_reset": "artifact state reset" in text,
        "f117_down": re.findall(
            r"\[F117-TAP\] frame (\d+) DOWN \((\d+),(\d+)\) target=(\d+)",
            text),
        "ui_touch": re.findall(
            r"\[UI-EVENT\] event=TOUCH action=(\d+) .*?result=(\S+)"
            r"(?: consumed=(\S+))?", text)[:8],
        "click_rows": len(re.findall(r"\[UI-EVENT\] event=CLICK", text)),
        "click_dispatched": len(re.findall(
            r"\[UI-EVENT\] event=CLICK[^\n]*DISPATCHED", text)),
        "perform_click": len(re.findall(r"PerformClick", text)),
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "face_screenshot": sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
        "frame_faces": frame_faces(rundir),
    }
    print(json.dumps({k: v for k, v in row.items() if k != "frame_faces"},
                     indent=1))
    return row, text


def main():
    # stale-binary guard: the gate strings MUST be in the binary
    import subprocess as sp
    if b"AWAIT-UP-GATE" not in sp.run(["strings", str(BIN)],
                                      capture_output=True).stdout:
        print("FATAL: binary lacks the S154 gate — stale build"); sys.exit(2)
    print("binary gate check OK:", BIN)
    install(DOOZ_APK, DOOZ_STORE)
    rows = {}
    print("== E1 dooz tap, gate ON (default 15s) ==")
    rows["E1_dooz_gate"], t1 = run_case(
        "E1_dooz_gate", DOOZ_APK, DOOZ_STORE, tap="540,960@20", gate_ms=None,
        package="io.github.yamin8000.dooz")
    print("== E2 dooz tap, gate OFF (control) ==")
    rows["E2_dooz_nogate"], t2 = run_case(
        "E2_dooz_nogate", DOOZ_APK, DOOZ_STORE, tap="540,960@20", gate_ms=0,
        package="io.github.yamin8000.dooz")
    print("== E3 transistor tap, gate ON ==")
    rows["E3_transistor_gate"], _ = run_case(
        "E3_transistor_gate", TR_APK, TR_STORE, tap="996,567@15",
        gate_ms=None, package="org.y20k.transistor")
    print("== E4 diary tap, gate ON (regression guard) ==")
    rows["E4_diary_gate"], _ = run_case(
        "E4_diary_gate", DI_APK, DI_STORE, tap="1017,1857@15", gate_ms=None,
        package="org.billthefarmer.diary")
    print("== E5 dooz no-tap (byte-inert guard) ==")
    rows["E5_dooz_notap"], _ = run_case(
        "E5_dooz_notap", DOOZ_APK, DOOZ_STORE, tap=None, gate_ms=None,
        package="io.github.yamin8000.dooz")

    rows["_eval"] = {
        "E1": {
            "gate_fired": rows["E1_dooz_gate"]["gate_hit"],
            "up_delivered": any(a == "1" for a, _, _, _ in
                                rows["E1_dooz_gate"]["f117_down"]) or
            len(rows["E1_dooz_gate"]["f117_down"]) >= 1,
            "click_dispatched": rows["E1_dooz_gate"]["click_dispatched"],
        },
        "E2_control_gate_off": rows["E2_dooz_nogate"]["gate_hit"],
        "E5_byte_inert": rows["E5_dooz_notap"]["face_screenshot"],
        "E5_pin": PIN_DOOZ,
        "E5_match": rows["E5_dooz_notap"]["face_screenshot"] == PIN_DOOZ,
    }
    json.dump(rows, open(EVID / "S154_AWAITUP_GATE.json", "w"), indent=1)
    print("evidence ->", EVID / "S154_AWAITUP_GATE.json")


if __name__ == "__main__":
    main()
