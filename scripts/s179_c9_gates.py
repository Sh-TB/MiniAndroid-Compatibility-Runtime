#!/usr/bin/env python3
"""s179_c9_gates.py — S179: byte-inert gates for the C9 per-law wave
(Coder-9 #521 phase-1: C9-1 BitmapFactory.Options density law, C9-2
AssetFileDescriptor data-offset law, C9-3 VectorDrawable intrinsic law).
REF = fresh same-host baseline build of main HEAD; NEW = patched binary.
CLAIM: all four titles byte-inert (dooz face must REMAIN a0fae9072313e2d1
REAL_APP_CONTENT — no flip back to the A17-default face)."""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s167_w6_gates as g
import s166_trains as s166

REF = Path(sys.argv[2]) if len(sys.argv) > 2 else None
g.REF = REF
g.NEW = BASE / "miniandroid/build/miniandroid"
g.OUT = BASE / "run_s179_c9"
g.EVID = BASE / "evidence/s179_c9"
g.OUT.mkdir(parents=True, exist_ok=True)
g.EVID.mkdir(parents=True, exist_ok=True)


def save(name, payload):
    json.dump(payload, open(g.EVID / name, "w"), indent=1, default=str)
    print("evidence ->", g.EVID / name)


if __name__ == "__main__":
    phase = sys.argv[1]
    out = g.EVID / "S179_C9_GATES.json"
    cur = {}
    if out.exists():
        cur = json.load(open(out))
    if phase in ("gates", "gates_anchors"):
        rows = {"microtimer": g.anchor_pair("microtimer"),
                "g2048": g.anchor_pair("g2048"),
                "opencalc": g.anchor_pair("opencalc")}
        cur.setdefault("anchors", {}).update(rows)
        for k, v in rows.items():
            r, n = v[k + "_ref"], v[k + "_new"]
            print(k, r["screenshot_face"], n["screenshot_face"],
                  "BYTE-EQUAL" if r["screenshot_face"] == n["screenshot_face"] else "DIVERGED")
    if phase in ("gates", "gates_dooz"):
        ctl = s166.dooz_run("c9_dz_ctl", g.REF, store_root=g.OUT)
        fix = s166.dooz_run("c9_dz_fix", g.NEW, store_root=g.OUT)
        cur["c9_dz_ctl"] = ctl
        cur["c9_dz_fix"] = fix
        cur["c9_dz_summary"] = s166.pair_summary(ctl, fix)
        print("dooz:", json.dumps(s166.pair_summary(ctl, fix))[:400])
    if phase in ("gates", "gates_tg"):
        tctl = s166.tg_run("c9_tg_ctl", g.REF, store_name="s179_tg")
        cur["c9_tg_ctl"] = tctl
        save("S179_C9_GATES.json", cur)
        tfix = s166.tg_run("c9_tg_fix", g.NEW, store_name="s179_tg")
        cur["c9_tg_fix"] = tfix
        cur["c9_tg_summary"] = s166.pair_summary(tctl, tfix)
        print("tg:", json.dumps(s166.pair_summary(tctl, tfix))[:400])
    save("S179_C9_GATES.json", cur)
