#!/usr/bin/env python3
"""s159_fieldslot.py — S159: verify the RECOVERED S158-W3 field-slot overlay.

Provenance: environment auto-commit 303ad5b1 (UUID message) swept up an
uncommitted lost-session implementation of the pinned dooz lever — the
field-slot fast path (S156 phase-B) on top of the S157-B cache hardening:
  W1 iput reuses the memo-banked s134 key (kills per-write concat+copy)
  W2 memo-banked s134_decl_is_dex predicate (kills per-write hash lookup)
  W3 iget/iget-object DEX-declared reads + iput writes via a dense per-object
     slot overlay (map stays storage of record; dual-write invariant)
Verification law: unverified local code = zero value until I run it.

Phase A (dooz 40%): dooz E5 no-tap on the overlay binary (fde53d47) with the
s158 /proc monitor. Success criteria (same as S158):
  face == 851cc1761a1dfcdf          -> dooz MOVED (board renders)
  face == 11a38a5aeeff45a6, wall moved >=20% vs 127s -> throughput lever
  face unchanged, wall flat         -> REJECTED
Phase B (anchor delta-inertness): microtimer/g2048/opencalc on BOTH the
overlay binary and the S157-B ref 908d5ba6, same fresh-store protocol ->
faces must be byte-identical BETWEEN BINARIES (delta-inert); microtimer
additionally must match the standing pin bbd350b6 (E5-flagged pin).

Usage: python3 scripts/s159_fieldslot.py dooz|anchors|collect
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s155_dooz_placement as s155
import s158_jemalloc_ab as s158
import s158_w5_gates as gates

OUT = BASE / "run_s159_fieldslot"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s156_record_loop"

W3 = BASE / "upload/_ma_local_backup/miniandroid_fieldslot_303ad5b1_fde53d47bd5b3845.bin"
REF = gates.REF

# S158 same-protocol controls (this VM, insurance binary 908d5ba6)
CTRL = {"face": "11a38a5aeeff45a6", "wall_s": 127.0, "rss_grow_mb_s": 1.87,
        "minflt_per_s": 477.0}

APKS = {
    "microtimer": (gates.MICRO_APK, "dubrowgn.microtimer"),
    "g2048": (gates.G2048_APK, "com.miniandroid.g2048"),
    "opencalc": (BASE / "upload/opencalculator_53.apk",
                 "com.darkempire78.opencalculator"),
}


def phase_dooz():
    s158.OUT = OUT          # run_arm artifacts -> run_s159_fieldslot/
    s158.BIN = W3
    s155.OUT = OUT
    row = s158.run_arm("W3_fieldslot", {}, max_seconds=110, frames=30)
    if row is None:
        print("DOOZ RUN FAILED")
        return
    face = row.get("screenshot_face")
    if face == s155.PIN_DOOZ:
        cls = "DOOZ MOVED — BOARD RENDERED"
    elif face == "11a38a5aeeff45a6":
        dw = (row.get("wall_s", 0) - CTRL["wall_s"]) / CTRL["wall_s"]
        cls = f"SPIN_FACE_PERSISTS wall_delta={dw:+.1%}"
    else:
        cls = f"UNEXPECTED_FACE {face}"
    row["classification"] = cls
    row["binary"] = "fde53d47bd5b3845 (field-slot overlay)"
    row["control_S158"] = CTRL
    rows = {}
    p = EVID / "S159_FIELDSLOT.json"
    if p.exists():
        rows = json.loads(p.read_text())
    rows["dooz"] = row
    json.dump(rows, open(p, "w"), indent=1, default=str)
    print(f"CLASSIFICATION: {cls}")


def phase_anchors():
    s155.OUT = OUT
    gates.OUT = OUT
    p = EVID / "S159_FIELDSLOT.json"
    rows = json.loads(p.read_text()) if p.exists() else {}
    out = rows.get("anchors", {})
    for name, (apk, pkg) in APKS.items():
        pair = {}
        for tag, b in ((f"{name}_ref", REF), (f"{name}_w3", W3)):
            store = OUT / f"store_{name}_{tag}/data"
            pair[tag] = gates.app_run(b, tag, apk, store, pkg,
                                      max_seconds=75)
            print(f"[{tag}] face={pair[tag]['screenshot_face']} "
                  f"wall={pair[tag]['wall_s']}s")
        fr, fw = (pair[f"{name}_ref"]["screenshot_face"],
                  pair[f"{name}_w3"]["screenshot_face"])
        pair["delta_inert"] = (fr is not None and fr == fw)
        if name == "microtimer":
            pair["pin_match"] = bool(fw and fw.startswith(gates.PINS["microtimer"]))
        out[name] = pair
        rows["anchors"] = out
        json.dump(rows, open(p, "w"), indent=1, default=str)
    for name, pair in out.items():
        print(f"{name}: delta_inert={pair['delta_inert']}"
              + (f" pin_match={pair.get('pin_match')}"
                 if "pin_match" in pair else ""))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dooz"
    if mode == "dooz":
        phase_dooz()
    elif mode == "anchors":
        phase_anchors()
    elif mode == "collect":
        p = EVID / "S159_FIELDSLOT.json"
        rows = json.loads(p.read_text())
        d = rows.get("dooz", {})
        print("dooz:", d.get("classification"))
        print("  face", d.get("screenshot_face"), "wall", d.get("wall_s"),
              "rss_grow", d.get("rss_grow_mb_s"), "minflt/s",
              d.get("minflt_per_s"))
        for name, pair in rows.get("anchors", {}).items():
            print(f"{name}: delta_inert={pair['delta_inert']}")
