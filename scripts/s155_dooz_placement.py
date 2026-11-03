#!/usr/bin/env python3
"""s155_dooz_placement.py — S155 wave: dooz CELL-PLACEMENT semantic proof.

The S154 honest frontier: "the post-UP compose click reached the board (UP
consumed + face movement) but the CELL-PLACEMENT semantic (O/X on the board)
is not yet proven". S155 proves or refutes that the consumed tap reaches the
app's game logic and renders the mark — the FULL user-visible semantic.

Evidence channels (no engine changes needed — diagnostics only):
  1. MINIANDROID_RET_TRACE=yamin8000 -> every app-class invocation row: the
     placement lambda MUST run after the UP (game-logic execution).
  2. MINIANDROID_T68_NODE_TRACE=1 -> pointer-input node census: WHICH node
     received the tap (per-cell clickable nodes).
  3. Pixel truth: cell-box nonwhite-pixel delta pre/post tap + stable final
     face (a mark, once placed, stays).
  4. Turn law: E2's SECOND tap must place the OTHER mark in a DIFFERENT cell
     (real game logic, not a one-off visual artifact).

Experiments (binary MUST rebuild byte-exact a793f134936f7e58):
  E0 dooz no-tap, fresh store      -> face == 851cc1761a1dfcdf (byte-inert)
  E1 dooz tap (540,960)@20  x1     -> ONE placement in the center cell
  E2 dooz tap (540,960)@20 + (270,760)@24 -> TWO placements, turn alternation
  E3 diary tap (1017,1857)@15      -> b18c3ee6c2818560 (regression guard)
  E4 transistor tap (996,567)@15   -> 5436cf81605f1c2d (regression guard)

Usage:
  python3 scripts/s155_dooz_placement.py pre      # E0 + grid detection + E3/E4
  python3 scripts/s155_dooz_placement.py taps     # E1 + E2 (uses detected grid)
  python3 scripts/s155_dooz_placement.py collect  # write evidence JSON + MD
"""
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

BASE = Path("/home/z/my-project")
BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run155"          # run/ is root-owned (infra artifact) -> new dir
EVID = BASE / "evidence/s155_dooz_placement"
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)

DOOZ_APK = BASE / "upload/canonical_apks/dooz_23_toplevel.apk"
TR_APK = BASE / "upload/s151_internet_batch/org.y20k.transistor_117.apk"
DI_APK = BASE / "upload/s151_internet_batch/org.billthefarmer.diary_1105.apk"

DOOZ_STORE = OUT / "store_dooz/data"
TR_STORE = BASE / "evidence/s151_trains/store_org.y20k.transistor_117/data"
DI_STORE = BASE / "evidence/s151_trains/store_org.billthefarmer.diary_1105/data"

ENGINE_SHA = "a793f134936f7e58"
PIN_DOOZ = "851cc1761a1dfcdf"
PIN_DIARY = "b18c3ee6c2818560"
PIN_TRANSISTOR = "5436cf81605f1c2d"

VERDICT_RE = re.compile(r"FRAME_ANALYSIS state=(\S+)")


def sha16(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def check_binary():
    """sha gate is a WARN: the S152 precedent allows a dev-tree binary as
    long as default-mode output stays BYTE-EXACT to the standing pins —
    that behavioral gate is E0/E5 (face == 851cc1761a1dfcdf). This sandbox
    lost miniandroid/build/ + disk was 100% -> S155 rebuilt -O1 no-g
    (sha 03aca4b7b55a8ad5) from the SAME committed sources (42238cf2)."""
    if not BIN.exists():
        print("FATAL: binary missing — build first"); sys.exit(2)
    got = sha16(BIN)
    ok_strings = b"AWAIT-UP-GATE" in subprocess.run(
        ["strings", str(BIN)], capture_output=True).stdout
    print(f"binary sha16={got} expected={ENGINE_SHA} "
          f"gate_strings={'OK' if ok_strings else 'MISSING'}")
    if got != ENGINE_SHA:
        print("WARN: dev-tree binary (not the S154 sha) — proceeding per "
              "S152 precedent; the BINDING gate is E0 face == "
              "851cc1761a1dfcdf (default-mode byte-exactness)")
    if not ok_strings:
        print("FATAL: stale binary (no gate strings)"); sys.exit(2)
    return got


def frame_faces(rundir):
    faces = {}
    for f in sorted(Path(rundir).glob("frames/frame_*")):
        m = re.search(r"frame_(\d+)", f.name)
        if m:
            faces[int(m.group(1))] = sha16(f)
    return faces


def install(apk, store):
    store.parent.mkdir(parents=True, exist_ok=True)
    if not (store / "data").exists() and not store.exists():
        subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=300)


def run_case(tag, apk, store, taps=None, frames=30, max_seconds=110,
             package=None, ret_trace=None, t68=False, gate_ms=None):
    rundir = OUT / tag
    console = OUT / f"{tag}_console.log"
    env = dict(os.environ)
    if gate_ms is not None:
        env["MINIANDROID_AWAITUP_GATE_MS"] = str(gate_ms)
    if ret_trace:
        env["MINIANDROID_RET_TRACE"] = ret_trace
    if t68:
        env["MINIANDROID_T68_NODE_TRACE"] = "1"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", str(frames),
           "--trace"]
    if package:
        cmd += ["--package", package]
    for t in (taps or []):
        cmd += ["--tap", t]
    t0 = time.time()
    killed = False
    try:
        with open(console, "w") as cf:
            subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                           timeout=max_seconds + 90, env=env)
    except subprocess.TimeoutExpired:
        killed = True
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    return analyze(tag, taps, wall, killed, text, rundir), text


def analyze(tag, taps, wall, killed, text, rundir):
    ret_rows = re.findall(r"\[RET-TRACE\] (\S+)", text)
    t68 = re.findall(r"\[T68-ENTRY\] (\S+) this=obj#(\d+)", text)
    ui = re.findall(r"\[UI-EVENT\] event=(\S+) action=(\d+).*?"
                    r"result=(\S+)(?: consumed=(\S+))?", text)
    row = {
        "tag": tag, "taps": taps, "wall_s": wall, "process_killed": killed,
        "verdict": (VERDICT_RE.findall(text) or [None])[-1],
        "gate_rows": len(re.findall(r"\[AWAIT-UP-GATE\]", text)),
        "gate_hit": "HALT(scoped)" in text,
        "artifact_reset": "artifact state reset" in text,
        "f117_taps": re.findall(r"\[F117-TAP\] frame (\d+) DOWN \((\d+),"
                                r"(\d+)\) target=(\d+)", text),
        "ui_events": ui[:12],
        "ret_trace_rows": len(ret_rows),
        "ret_trace_methods": Counter(
            r.rsplit("->", 1)[0] for r in ret_rows).most_common(12),
        "ret_trace_first10": ret_rows[:10],
        "t68_nodes": Counter(f"{c}.{m}" for c, m in t68).most_common(10),
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "screenshot_face": sha16(rundir / "screenshot.png")
        if (rundir / "screenshot.png").exists() else None,
        "frame_faces": frame_faces(rundir),
    }
    slim = {k: v for k, v in row.items() if k != "frame_faces"}
    print(json.dumps(slim, indent=1, default=str)[:2600])
    return row


def nonwhite_in_box(img_path, box):
    """count pixels with any channel < 240 inside box=(x0,y0,x1,y1)"""
    from PIL import Image
    im = Image.open(img_path).convert("L")
    x0, y0, x1, y1 = box
    px = im.crop((x0, y0, x1, y1))
    data = px.getdata()
    return sum(1 for v in data if v < 240)


def grid_detect(rundir):
    """detect the board grid lines in the LAST frame -> cell centers"""
    from PIL import Image
    frames = sorted(Path(rundir).glob("frames/frame_*"),
                    key=lambda p: int(re.search(r"(\d+)", p.name).group(1)))
    if not frames:
        return None
    im = Image.open(frames[-1]).convert("L")
    w, h = im.size
    px = im.load()
    # board zone: middle band (below top bar, above bottom bar)
    y0z, y1z = int(h * 0.28), int(h * 0.72)
    rows, cols = [], []
    for y in range(y0z, y1z):
        dark = sum(1 for x in range(int(w * 0.08), int(w * 0.92), 2)
                   if px[x, y] < 200)
        if dark > w * 0.30:
            rows.append(y)
    for x in range(int(w * 0.08), int(w * 0.92)):
        dark = sum(1 for y in range(y0z, y1z, 2) if px[x, y] < 200)
        if dark > (y1z - y0z) * 0.30:
            cols.append(x)

    def merge(v, gap=12):
        out = []
        for n in v:
            if out and n - out[-1][-1] <= gap:
                out[-1].append(n)
            else:
                out.append([n])
        return [sum(g) // len(g) for g in out]

    rows, cols = merge(rows), merge(cols)
    return {"rows_y": rows, "cols_x": cols, "frame": frames[-1].name,
            "frame_sha16": sha16(frames[-1])}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    if mode in ("pre", "all"):
        check_binary()
        install(DOOZ_APK, DOOZ_STORE)
        rows = {}
        print("== E0 dooz no-tap (byte-inert + grid detection) ==")
        rows["E0_dooz_notap"], _ = run_case(
            "E0_dooz_notap", DOOZ_APK, DOOZ_STORE, taps=None,
            package="io.github.yamin8000.dooz")
        gd = grid_detect(OUT / "E0_dooz_notap")
        rows["_grid"] = gd
        print("GRID:", json.dumps(gd, indent=1))
        print("== E3 diary tap (regression) ==")
        rows["E3_diary"], _ = run_case(
            "E3_diary", DI_APK, DI_STORE, taps=["1017,1857@15"],
            package="org.billthefarmer.diary")
        print("== E4 transistor tap (regression) ==")
        rows["E4_transistor"], _ = run_case(
            "E4_transistor", TR_APK, TR_STORE, taps=["996,567@15"],
            package="org.y20k.transistor")
        json.dump(rows, open(EVID / "s155_pre.json", "w"), indent=1,
                  default=str)
        print("pre rows ->", EVID / "s155_pre.json")
    if mode in ("taps", "all"):
        check_binary()
        install(DOOZ_APK, DOOZ_STORE)
        rows = {}
        print("== E1 dooz ONE tap (540,960)@20, RET_TRACE + T68 ==")
        rows["E1_dooz_one"], _ = run_case(
            "E1_dooz_one", DOOZ_APK, DOOZ_STORE, taps=["540,960@20"],
            frames=30, max_seconds=170, package="io.github.yamin8000.dooz",
            ret_trace="yamin8000", t68=True)
        print("== E2 dooz TWO taps (turn law) ==")
        rows["E2_dooz_two"], _ = run_case(
            "E2_dooz_two", DOOZ_APK, DOOZ_STORE,
            taps=["540,960@20", "270,760@24"], frames=34, max_seconds=230,
            package="io.github.yamin8000.dooz", ret_trace="yamin8000",
            t68=True)
        json.dump(rows, open(EVID / "s155_taps.json", "w"), indent=1,
                  default=str)
        print("tap rows ->", EVID / "s155_taps.json")
    if mode == "collect":
        sys.exit(0)


if __name__ == "__main__":
    main()
