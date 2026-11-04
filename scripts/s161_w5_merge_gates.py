#!/usr/bin/env python3
"""s161_w5_merge_gates.py — S161: merge-gate the S158-APPROVED W5 delta INTO main.

User directive (2026-11-04): coders' achievements that I verified get added
to my own tree. The #514 W5-only delta was verified تایید at delta level in
S158 (clean-apply on eb72df8b, compile, dooz byte-inert, CB normalized A/B
IDENTICAL, microtimer pin-exact, g2048 harness-artifact resolved) but was
never merged into my main. This session applies it to main (source state is
unchanged since eb72df8b -> git apply --check CLEAN re-confirmed), rebuilds,
and re-runs the three gates on the MERGED tree with the new binary
512517269d9634a1:

  Gate B  dooz E5 no-tap      -> face MUST be 11a38a5aeeff45a6 (byte-inert)
  Gate E  microtimer + g2048  -> microtimer == standing pin bbd350b6;
                                 g2048 W5-merged == REF byte-exact
  Gate C  ConnectBot stderr   -> normalized multiset A/B vs REF 908d5ba6
                                 (S158 method: strip ASLR/RSS/ms/paths/ns +
                                 sort; same-binary-twice control proved raw
                                 stderr pins impossible)

Usage: python3 scripts/s161_w5_merge_gates.py dooz|anchors|cb|collect
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s155
import s158_jemalloc_ab as s158
import s158_w5_gates as gates

OUT = BASE / "run_s161_w5merge"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s156_record_loop"

W5M = BASE / "upload/_ma_local_backup/miniandroid_main_w5merged_edfb7760_512517269d9634a1.bin"
REF = gates.REF
CB_APK = gates.CB_APK

VOLATILE = [
    (re.compile(r"0x[0-9a-f]{6,}"), "0xPTR"),          # ASLR pointers
    (re.compile(r"rss_mb=[0-9.]+"), "rss_mb=X"),
    (re.compile(r"RSS=[0-9.]+ MB"), "RSS=X MB"),   # [MEM] method_exit rows
    (re.compile(r"=\d+ ms\b"), "=X ms"),
    (re.compile(r"ms=\d+"), "ms=X"),
    (re.compile(r"/home/z/\S+"), "PATH"),
    (re.compile(r"\b\d{10,}\b"), "NS"),                # ns epoch stamps
    (re.compile(r"engine=0x[0-9a-f]+"), "engine=0xX"),
]


def norm_lines(text):
    out = []
    for ln in text.splitlines():
        for rx, repl in VOLATILE:
            ln = rx.sub(repl, ln)
        out.append(ln.strip())
    return sorted(out)


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def gate_dooz():
    s158.OUT = OUT
    s158.BIN = W5M
    s155.OUT = OUT
    row = s158.run_arm("w5merged_dooz_notap", {}, max_seconds=110, frames=30)
    row["binary"] = "512517269d9634a1 (main+W5 merged)"
    row["gate"] = "B"
    row["pass"] = row.get("screenshot_face") == "11a38a5aeeff45a6"
    print(f"Gate B: face={row.get('screenshot_face')} pass={row['pass']} "
          f"wall={row.get('wall_s')}")
    return row


def gate_anchors():
    gates.OUT = OUT
    s155.OUT = OUT
    out = {}
    for name, apk, pkg in (
            ("microtimer", gates.MICRO_APK, "dubrowgn.microtimer"),
            ("g2048", gates.G2048_APK, "com.miniandroid.g2048")):
        pair = {}
        for tag, b in ((f"{name}_ref", REF), (f"{name}_w5m", W5M)):
            store = OUT / f"store_{name}_{tag}/data"
            pair[tag] = gates.app_run(b, tag, apk, store, pkg,
                                      max_seconds=75)
            print(f"[{tag}] face={pair[tag]['screenshot_face']} "
                  f"wall={pair[tag]['wall_s']}s")
        fr, fw = (pair[f"{name}_ref"]["screenshot_face"],
                  pair[f"{name}_w5m"]["screenshot_face"])
        pair["delta_inert"] = (fr is not None and fr == fw)
        if name == "microtimer":
            pair["pin_match"] = bool(fw and fw.startswith(gates.PINS["microtimer"]))
        out[name] = pair
    return out


def gate_cb():
    gates.OUT = OUT
    rows = {}
    errs = {}
    for tag, b in (("cb_ref", REF), ("cb_w5m", W5M)):
        store = OUT / f"store_cb_{tag}/data"
        rows[tag] = gates.app_run(b, tag, CB_APK, store,
                                  "org.connectbot", max_seconds=75)
        errs[tag] = (OUT / f"{tag}.err").read_text(errors="replace")
    nr, nw = norm_lines(errs["cb_ref"]), norm_lines(errs["cb_w5m"])
    identical = (nr == nw)
    diff_sample = []
    if not identical:
        a, bset = set(nr), set(nw)
        diff_sample = sorted(a - bset)[:6] + sorted(bset - a)[:6]
    return {"cb_ref": rows["cb_ref"], "cb_w5m": rows["cb_w5m"],
            "normalized_identical": identical,
            "diff_sample": diff_sample}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "collect"
    p = EVID / "S161_W5_MERGE_GATES.json"
    rows = json.loads(p.read_text()) if p.exists() else {}
    if mode == "dooz":
        rows["gate_B_dooz"] = gate_dooz()
    elif mode == "anchors":
        rows["gate_E_anchors"] = gate_anchors()
    elif mode == "cb":
        rows["gate_C_cb"] = gate_cb()
    json.dump(rows, open(p, "w"), indent=1, default=str)
    if mode == "collect":
        b = rows.get("gate_B_dooz", {}).get("pass")
        e = rows.get("gate_E_anchors", {})
        c = rows.get("gate_C_cb", {})
        print(f"Gate B dooz byte-inert: {b}")
        for k, v in (e or {}).items():
            print(f"Gate E {k}: delta_inert={v.get('delta_inert')}"
                  + (f" pin_match={v.get('pin_match')}" if "pin_match" in v else ""))
        print(f"Gate C CB normalized identical: {c.get('normalized_identical')}")
        if c.get("diff_sample"):
            print("diff sample:", c["diff_sample"][:8])
        verdict = "POSITIVE" if (b and c.get("normalized_identical")
                                 and all(v.get("delta_inert")
                                         for v in (e or {}).values())) \
                  else "NEGATIVE/INCOMPLETE"
        rows["verdict"] = verdict
        json.dump(rows, open(p, "w"), indent=1, default=str)
        print("MERGE-GATE VERDICT:", verdict)


if __name__ == "__main__":
    main()
