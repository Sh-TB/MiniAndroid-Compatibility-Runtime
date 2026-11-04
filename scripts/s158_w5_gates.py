#!/usr/bin/env python3
"""s158_w5_gates.py — S158: Coder-4 #514 W5 (F-C4-566/567/568) merge-gate slice.

The w5_only delta (314-line block from comment 6616230230) applied CLEAN on
detached HEAD eb72df8b (no W2/W3/W4 needed) and compiled (build_w5/miniandroid).

Their 4APP stderr sha16s are FULL-STACK-relative (W2+W3+W4+W5) — NOT
reproducible with the w5-only delta. What IS verifiable here (the delta
contract):
  Gate B (byte-inertness on my frontier): dooz E5 no-tap on the W5 binary
          -> face MUST be the standing spin face 11a38a5aeeff45a6.
  Gate C (CB delta-inertness, their "unchanged family" claim): ConnectBot
          stderr A/B — unpatched 908d5ba6 vs W5-only binary, same fresh
          store/flags -> stderr sha16 must be IDENTICAL.
  Gate E (anchor smoke): microtimer + g2048 x1 on the W5 binary -> faces
          byte-exact vs standing pins (bbd350b6 / f43face08).
  Gate D (F-C4-566 substance): needs the TB APK (absent since S153) ->
          coder-attested only, NOT verified here.

Usage: python3 scripts/s158_w5_gates.py dooz|cb|anchors|collect
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s155

W5 = Path("/home/z/w5_verify/miniandroid/build_w5/miniandroid")
REF = BASE / "upload/_ma_local_backup/miniandroid_s157b_gated_908d5ba61aa62485.bin"
OUT = BASE / "run_s158_w5"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s156_record_loop"

CB_APK = BASE / "upload/fdroid_batch/org.connectbot_11101000.apk"
MICRO_APK = BASE / "upload/canonical_apks/dubrowgn.microtimer_8.apk"
G2048_APK = BASE / "upload/s80_games/build_2048/g2048_v1.0_vc1.apk"

# pins as recorded in the wall ledgers: 8-hex prefixes (face.startswith(pin))
PINS = {"microtimer": "bbd350b6", "g2048": "f43face08"}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def app_run(bin_path, tag, apk, store, package, max_seconds=75):
    """their stderr-capture pattern: run, stderr -> separate .err file"""
    store = Path(store)
    rundir = OUT / tag
    if not store.exists():
        subprocess.run([str(bin_path), "install", str(apk),
                        "--data-root", str(store)], capture_output=True,
                       timeout=300)
    errfile = OUT / f"{tag}.err"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "--package", package,
           "-o", str(rundir), "--max-seconds", str(max_seconds)]
    env = dict(os.environ)
    env.pop("MINIANDROID_S155_APPLY", None)
    t0 = time.time()
    with open(errfile, "w") as ef:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=ef,
                       timeout=max_seconds + 60, env=env)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    return {
        "tag": tag, "wall_s": wall, "stderr_sha16": sha16(errfile),
        "stderr_lines": sum(1 for _ in open(errfile, errors="replace")),
        "screenshot_face": sha16(shot) if shot.exists() else None,
    }


def gate_dooz():
    s155.OUT = OUT
    store = OUT / "store_dooz_w5/data"
    subprocess.run(["rm", "-rf", str(OUT / "store_dooz_w5")], check=False)
    r = subprocess.run([str(W5), "install", str(s155.DOOZ_APK),
                        "--data-root", str(store)], capture_output=True,
                       timeout=300)
    assert r.returncode == 0, r.stderr[-300:]
    rundir = OUT / "w5_dooz_notap"
    console = OUT / "w5_dooz_notap_console.log"
    env = dict(os.environ)
    env.pop("MINIANDROID_S155_APPLY", None)
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run([str(W5), "run", "--execution-mode", "real-dalvik",
                        "--data-root", str(store), "-o", str(rundir),
                        "--max-seconds", "110", "--frames", "30", "--trace",
                        "--package", "io.github.yamin8000.dooz"],
                       stdout=cf, stderr=subprocess.STDOUT, timeout=200,
                       env=env)
    wall = round(time.time() - t0, 1)
    text = console.read_text(errors="replace")
    row = s155.analyze("w5_dooz_notap", None, wall, False, text, rundir)
    face = row.get("screenshot_face")
    ok = face == "11a38a5aeeff45a6"
    print(f"GATE B (dooz byte-inert): face={face} "
          f"{'PASS' if ok else 'FAIL — DRIFT'}")
    return {"gate_b_dooz": {**{k: v for k, v in row.items()
                               if k != "frame_faces"},
                            "gate_pass": ok}}


def gate_cb():
    rows = {}
    for name, binp in (("ref_908d5ba6", REF), ("w5_only", W5)):
        rows[name] = app_run(binp, f"cb_{name}", CB_APK,
                             OUT / f"store_cb_{name}/data",
                             "org.connectbot")
        print(f"CB {name}: stderr_sha16={rows[name]['stderr_sha16']} "
              f"lines={rows[name]['stderr_lines']} "
              f"wall={rows[name]['wall_s']}s "
              f"face={rows[name]['screenshot_face']}")
    same = (rows["ref_908d5ba6"]["stderr_sha16"]
            == rows["w5_only"]["stderr_sha16"])
    print(f"GATE C (CB delta-inert): {'PASS' if same else 'FAIL — DRIFT'}")
    return {"gate_c_cb": {**rows, "gate_pass": same}}


def gate_anchors():
    res = {}
    for name, apk, pkg in (("microtimer", MICRO_APK, "dubrowgn.microtimer"),
                           ("g2048", G2048_APK, "com.miniandroid.g2048")):
        row = app_run(W5, f"w5_{name}", apk, OUT / f"store_{name}/data", pkg,
                      max_seconds=60)
        pin = PINS[name]
        face = row["screenshot_face"] or ""
        ok = face.startswith(pin)
        res[name] = {**row, "pin": pin, "gate_pass": ok}
        print(f"ANCHOR {name}: face={row['screenshot_face']} pin={pin} "
              f"{'PASS' if ok else 'FAIL — DRIFT'}")
    return {"gate_e_anchors": res}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = EVID / "S158_W5_GATES.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if mode in ("dooz", "all"):
        data.update(gate_dooz())
    if mode in ("cb", "all"):
        data.update(gate_cb())
    if mode in ("anchors", "all"):
        data.update(gate_anchors())
    json.dump(data, open(path, "w"), indent=1, default=str)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
